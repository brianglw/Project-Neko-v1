import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import SendIcon from '@mui/icons-material/Send';
import {useState, useEffect} from 'react'
import api from '../services/api.js'

const Home = () => {
    const [msg, setMsg] = useState("")
    const [history, setHistory] = useState([])
    const [chatLog, setChatLog] = useState([])
    const [doesLoading, setDoesLoading] = useState(true)
    const [doesSaving, setDoesSaving] = useState(false)
    const [doesLogging, setDoesLogging] = useState(false)

    const load = () => {
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
    }

    // useEffect(() => {
        // updates history (short-term) and chatlog DB each chat state changes
        const handleDumpDB = async (data, filename) => {
            await api.post(`/dumpDB/${filename}`, {'memo': data})
            .then((response) => {
                console.log(`Home.jsx ${handleDumpDB.name} history`, `sent ${JSON.stringify({'memo': data})}`, `received ${JSON.stringify(response.data)}`); 
            })
            .catch((error) => {
                console.error(`Home.jsx ${handleDumpDB.name}`, error);
            });
        }
    //     }
    //     if (history.length > 0) {
    //         handleDumpDB(history.slice(-2), "history")
    //         // console.log("handleDumpDB success")
    //     }
    // }, [history])
    

    useEffect(() => {
        //updates history (short-term) and chatlog DB each chat state changes
        const handleDumpDB = async (data, filename) => {
            await api.post(`/dumpDB/${filename}`, {'memo': data})
            .then((response) => {
                console.log(`Home.jsx ${handleDumpDB.name} chatlog`, `sent ${JSON.stringify({'memo': data})}`, `received ${JSON.stringify(response.data)}`)
            })
            .catch((error) => {
                console.error(`Home.jsx ${handleDumpDB.name}`, error);
            });
        }
        if (chatLog.length > 0) {
            handleDumpDB(chatLog.slice(-2), "chatlog")
        }
    }, [chatLog])

    const handleReset = async () => { //clears DB records and empties chat state
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

    const handleTextChange = (e) => { //updates state from textbox value as user enters
        e.preventDefault()
        setMsg(e.target.value)
    }

    const handleChat = async () => { 
        const formatted_msg = {'role': 'user', 'content': msg}
        // console.log("Chatting with current history...", history)
        await api.post("/chat", {'memo': [...history, formatted_msg]})
        .then((response) => {
            console.log(`Home.jsx ${handleChat.name}`, response.data)
            if (response.data['memo'].length > 0) {
                setHistory((prev) => (response.data['memo']))
                setChatLog((prev) => ([...prev, response.data['memo'].at(-1)]))
                handleDumpDB(response.data['memo'].slice(-2), "history")
                // console.log("Home.jsx handleChat(): Files saved")
            } 
            // console.log("History after reply", history)
            // console.log("Chatlog after reply", chatLog)
            // console.log("Fetching /chat API response", response.data); 
        })
        .catch((error) => {
            console.error(`Home.jsx ${handleChat.name}`, error);
        });
        setMsg("")
    }

    const handleSubmit = (e) => {
        try {
            e.preventDefault()
            if (msg.trim().toLowerCase() == "/reset") {
                handleReset()
            } else {
                handleChat()
            }
        } catch (e) {
            console.log(`Home.jsx ${handleSubmit.name}`, e)
        }
    }

    const History = () => {
        return (
            <div>
                {history.length === 0 ? <h1>Empty</h1> : 
                history.map((msg) => {
                    return <p>{`${msg.role}: ${msg.content}`}</p>
                })
                }
            </div>
        )
    }

    load()

    return (
        <main>
            <form id="send" onSubmit={handleSubmit}>
                <TextField
                    fullWidth
                    id="filled-multiline-static"
                    label="Chat"
                    multiline
                    rows={4}
                    placeholder='Type your message here'
                    variant="filled"
                    onChange={handleTextChange}
                    value={msg}
                />
                <Button type='submit' variant="contained" >
                    <SendIcon />
                </Button>
                <History />
            </form>
        </main>
    )
}

export default Home