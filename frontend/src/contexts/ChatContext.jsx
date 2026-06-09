import {useState, useEffect, createContext, useContext} from 'react'
import api from '../services/api.js'

const ChatContext = createContext()

export const useChatContext = () => useContext(ChatContext)

export const ChatProvider = ({children}) => {
    const [msg, setMsg] = useState("")
    const [history, setHistory] = useState([])
    const [chatLog, setChatLog] = useState([])
    const [isLoading, setIsLoading] = useState(false)

    useEffect(()=> { //creates connection to an existing db, or creates new one if doesn't exist
        const createNewDB = async() => {
            await api.post("/new").then((response) => {
                // console.log(response.data); // Parsed JSON object/array
            })
            .catch((error) => {
                console.error(`Home.jsx ${createNewDB.name}`, error);
            });
        }
        const handleLoadDB = async(filename) => {
            await api.get(`/loadDB/${filename}`)
            .then((response) => {
                console.log(`Home.jsx ${handleLoadDB.name}`, response.data); // Parsed JSON object/array
                setHistory(response.data['memo'])
            })
            .catch((error) => {
                console.error("Error:", error);
            });
        }
        createNewDB()
        handleLoadDB("history")
    }, [])

    const handleDumpDB = async (data, filename) => {
        await api.post(`/dumpDB/${filename}`, {'memo': data})
        .then((response) => {
            console.log(`Home.jsx ${handleDumpDB.name} history`, `sent ${JSON.stringify({'memo': data})}`, `received ${JSON.stringify(response.data)}`); 
        })
        .catch((error) => {
            console.error(`Home.jsx ${handleDumpDB.name}`, error);
        });
    }

    const handleReset = async () => { //clears DB records and empties chat state
        if (!isLoading) {
            await api.post("/reset")
                .then((response) => {
                    console.log(`Home.jsx ${handleReset.name}`, response.data);
                    setHistory([])
                    setChatLog([]) 
                })
                .catch((error) => {
                    console.error("Error:", error);
                }
            );
        }
    }

    const handleClearChat = () => {
        setMsg("")        
    }

    const handleKeyEvent = (e) => {
        if (!isLoading && e.key === 'Enter') {
            handleSubmit(e)
        } else if (!isLoading && e.key === 'Escape') {
            handleClearChat()
        }     
    }

    const handleTextChange = (e) => { //updates state from textbox value as user enters
        setMsg(e.target.value)
    }

    const handleChat = async () => { 
        if (!isLoading) {
            setIsLoading(true)
            const formatted_msg = {'role': 'user', 'content': msg}
            setMsg("")
            // console.log("Chatting with current history...", history)
            await api.post("/chat", {'memo': [...history, formatted_msg]})
            .then((response) => {
                console.log(`Home.jsx ${handleChat.name}`, response.data)
                if (response.data['memo'].length > 0) {
                    setHistory((prev) => (response.data['memo']))
                    setChatLog((prev) => ([...prev, response.data['memo'].at(-1)]))
                    handleDumpDB(response.data['memo'].slice(-2), "history")
                    handleDumpDB(response.data['memo'].slice(-2), "chatlog")
                    // console.log("Home.jsx handleChat(): Files saved")
                } 
            })
            .catch((error) => {
                console.error(`Home.jsx ${handleChat.name}`, error);
            });
        }
    }

    const handleSubmit = (e) => {
        try {
            e.preventDefault()
            if (msg.trim().toLowerCase() === "/reset") {
                handleReset()
            } else {
                handleChat()
                setIsLoading(false)
            }
        } catch (e) {
            console.log(`Home.jsx ${handleSubmit.name}`, e)
        }
    }

    const props = {
        msg, 
        setMsg,
        history,
        setHistory,
        chatLog,
        setChatLog,
        isLoading,
        setIsLoading,
        handleDumpDB,
        handleReset,
        handleClearChat,
        handleKeyEvent,
        handleTextChange,
        handleChat,
        handleSubmit
    }
    return <ChatContext.Provider value={props}>
        {children}
    </ChatContext.Provider>
}