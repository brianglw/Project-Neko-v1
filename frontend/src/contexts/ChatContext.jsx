import {useState, useEffect, createContext, useContext} from 'react'
import api from '../services/api.js'
import shoyuAvatarUrl from '../assets/shoyu_neutral2.jpg'
import capyAvatarUrl from '../assets/capybara.png'

const ChatContext = createContext()

export const useChatContext = () => useContext(ChatContext)

export const ChatProvider = ({children}) => {
    const [msg, setMsg] = useState("")
    const [history, setHistory] = useState([])
    const conversationId = 'conv-practice'
    // const [isLoading, setIsLoading] = useState(false)

    useEffect(()=> { //creates connection to an existing db, or creates new one if doesn't exist
        const createNewDB = async() => {
            await api.post("/new").then(() => {
                // Database tables are created if they do not already exist.
            })
            .catch((error) => {
                console.error(`Home.jsx ${createNewDB.name}`, error);
            });
        }
        const handleLoadDB = async(filename) => {
            await api.get(`/loadDB/${filename}`)
            .then((response) => {
                const resp = response.data?.memo ?? []
                console.log(`Home.jsx ${handleLoadDB.name}`, response.data.memo); // Parsed JSON object/array
                const texts = resp.map(msg => {
                    const text = msg?.parts?.find((part) => part.type === 'text')?.text ?? ''
                    console.log({
                        id: msg?.id,
                        conversationId: msg?.conversationId,
                        role: msg?.role,
                        author: msg?.author,
                        createdAt: msg?.createdAt,
                        text,
                    })
                    return createTextMessage({
                        id: msg?.id,
                        conversationId: msg?.conversationId ?? conversationId,
                        role: msg?.role,
                        author: msg?.author,
                        status: msg?.status,
                        createdAt: msg?.createdAt,
                        text,
                    })
                })
                console.log(texts)
                setHistory(texts)
            })
            .catch((error) => {
                console.error("Error:", error);
            });
        }
        createNewDB()
        handleLoadDB("history")
    // Only load persisted chat once when the provider mounts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    function createAvatarDataUrl(label, background, foreground = '#ffffff') {
        const svg = `<svg width="96" height="96" viewBox="0 0 96 96">
        <rect rx="24" fill="${background}"/>
        <text x="50%" y="54%" dominant-baseline="middle" text-anchor="middle" font-family="Arial, sans-serif" font-size="28" font-weight="600" fill="${foreground}">
        ${label}
        </text>
        </svg>`;

        return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
    }

    const demoUsers = {
        you: {
            id: '06',
            displayName: 'You',
            avatarUrl: capyAvatarUrl,
            isOnline: true,
            role: 'user',
        },
        shoyu: {
            id: '05',
            displayName: 'Shoyu',
            avatarUrl: shoyuAvatarUrl,
            isOnline: true,
            role: 'assistant',
        },
    };

    function createTextMessage(params) {
        const {
            id = `msg-${crypto.randomUUID()}`,
            conversationId: msgConversationId = conversationId,
            role = 'user',
            text,
            createdAt = new Date().toISOString(),
            author: providedAuthor,
            status = 'sent',
        } = params;
        const author = role === 'assistant' ? demoUsers.shoyu : (providedAuthor ?? demoUsers.you)

        return {
            id,
            conversationId: msgConversationId,
            role,
            status,
            createdAt: typeof createdAt === 'string' ? createdAt : createdAt.toISOString(),
            author,
            parts: [{ type: 'text', text }],
        };
    }

    function normalizeChatMessage(message) {
        const text = message?.parts
            ?.filter((part) => part.type === 'text')
            ?.map((part) => part.text ?? '')
            ?.join('')
            ?.trim()

        if (!text) {
            throw new Error('Cannot send an empty chat message')
        }

        return createTextMessage({
            id: message?.id,
            conversationId: message?.conversationId,
            role: message?.role ?? 'user',
            status: message?.status ?? 'sent',
            createdAt: message?.createdAt,
            author: message?.author,
            text,
        })
    }

    function normalizeChatHistory(messages) {
        return messages.map((message) => normalizeChatMessage(message))
    }

    const handleDumpDB = async (data, filename) => {
        await api.post(`/dumpDB/${filename}`, {'memo': data})
        .then((response) => {
            console.log(`Home.jsx ${handleDumpDB.name} history`, `sent ${JSON.stringify({'memo': data})}`, `received ${JSON.stringify(response.data)}`); 
        })
        .catch((error) => {
            console.error(`Home.jsx ${handleDumpDB.name}`, error);
        });
    }

    // const handleReset = async () => { //clears DB records and empties chat state
    //     await api.post("/reset")
    //         .then((response) => {
    //             console.log(`Home.jsx ${handleReset.name}`, response.data);
    //             setHistory([])
    //             setChatLog([])
    //         })
    //         .catch((error) => {
    //             console.error("Error:", error);
    //         }
    //     );
    // }


    // // const handleClearChat = () => {
    // //     setMsg("")
    // // }

    // // const handleKeyEvent = (e) => {
    // //     if (e.key === 'Enter') {
    // //         handleSubmit(e)
    // //     } else if (e.key === 'Escape') {
    // //         handleClearChat()
    // //     }
    // // }

    // // const handleTextChange = (e) => { //updates state from textbox value as user enters
    // //     setMsg(e.target.value)
    // // }

    const handleChat = async (message) => {
        let hist
        console.log("chat() history", history)
        const formatted_msg = normalizeChatMessage(message)
        // const texts = history.map(msg => {
        //     return {'id': msg['id'], 'conversationId': msg['conversationId'], 'status': msg['status'], 'createdAt': msg['createdAt'], 'author': msg['author'], 'parts': [{'type': 'text', 'text': msg['text']}]}
        // })
        const normalizedHistory = normalizeChatHistory(history)
        const payload = {'memo': [...normalizedHistory, formatted_msg]}
        console.log('chat() texts', payload)
        // setMsg("")
        // console.log("Chatting with current history...", history)
        await api.post("/chat", payload)
        .then(async (response) => {
            console.log(`Home.jsx ${handleChat.name}`, response.data)
            if (response.data?.memo?.length > 0) {
                hist = response.data
                // setHistory((prev) => (response.data['memo']))
                await Promise.all([
                    handleDumpDB(response.data['memo'].slice(-2), "history"),
                    handleDumpDB(response.data['memo'].slice(-2), "chatlog"),
                ])
                // console.log("Home.jsx handleChat(): Files saved")
            }
        })
        .catch((error) => {
            console.error(`Home.jsx ${handleChat.name}`, error);
            throw error
        });
        return hist
    }

    // const handleSubmit = (e) => {
    //     try {
    //         e.preventDefault()
    //         if (msg.trim().toLowerCase() === "/reset") {
    //             handleReset()
    //         } else {
    //             handleChat()
    //         }
    //     } catch (e) {
    //         console.log(`Home.jsx ${handleSubmit.name}`, e)
    //     }
    // }

    const props = {
        msg, 
        setMsg,
        history,
        setHistory,
        createAvatarDataUrl,
        createTextMessage,
        handleDumpDB,
        handleChat,
    }
    return <ChatContext.Provider value={props}>
        {children}
    </ChatContext.Provider>
}