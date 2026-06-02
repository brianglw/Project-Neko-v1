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

    useEffect(()=> { //calls loadDb endpoint
        const createNewDB = async() => {
            await api.post("/new").then((response) => {
                console.log(response.data); // Parsed JSON object/array
            })
            .catch((error) => {
                console.error("Error:", error);
            });
        }
        const handleLoadDB = async(filename) => {
            await api.get(`/loadDB/${filename}`)
            .then((response) => {
                console.log(response.data); // Parsed JSON object/array
                setHistory(response.data['list'])
            })
            .catch((error) => {
                console.error("Error:", error);
            });
        }
        if (doesLoading) {
            createNewDB()
            handleLoadDB("history")
            setDoesLoading(false)
        }
    }, [])

    useEffect(()=> { //calls dumpDB endpoint
        const handleDumpDB = async (data, filename) => {
            await api.post(`/dumpDB/${filename}`, {list: data})
            .then((response) => {
                console.log("Dumping history into db", response.data); 
            })
            .catch((error) => {
                console.error("Error:", error);
            });
        }
        if (doesSaving) {
            handleDumpDB(history, "history")
            setDoesSaving(false)
        }
        if (doesLogging) {
            const last_i = history.length - 1
            handleDumpDB(history[last_i], "chatlog")
            setDoesLogging(false)
        }
    }, [history, chatLog])

    const handleReset = async () => {
        await api.post("/reset")
            .then((response) => {
                console.log(response.data);
                setHistory([])
                setChatLog([]) 
            })
            .catch((error) => {
                console.error("Error:", error);
            }
        );
    }
    const handleTextChange = (e) => {
        e.preventDefault()
        setMsg(e.target.value)
    }
    const handleChat = async () => {
        const formatted_msg = {'role': 'user', 'content': msg}
        setDoesSaving(true)
        setDoesLogging(true)
        setHistory(prev => [...prev, formatted_msg])
        setChatLog(prev => [...prev, formatted_msg])
        console.log("Chatting with current history...", history)
        await api.post("/chat", {'list': history})
        .then((response) => {
            setHistory(prev => [...history,...response.data['list']])
            setChatLog(prev => [...prev, response.data['list']])
            console.log("Fetching /chat API response", response.data); 
        })
        .catch((error) => {
            console.error("Error:", error);
        });
        setMsg("")
        console.log("After reply", history)
    }
    const handleSubmit = (e) => {
        e.preventDefault()
        if (msg.trim().toLowerCase() == "/reset") {
            handleReset()
        } else {
            handleChat()
        }
    }

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
                <div>
                    {history == [] ? <h1>Empty</h1> : history.map((msg) => {
                        return <p>{`${msg.role}: ${msg.content}`}</p>
                    })}
                </div>
            </form>
        </main>
    )
}

export default Home