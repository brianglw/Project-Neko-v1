import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import SendIcon from '@mui/icons-material/Send';
import {useState, useEffect} from 'react'
import api from '../services/api.js'

const Home = () => {
    const [msg, setMsg] = useState("")
    const [history, setHistory] = useState([])
    const [chatLog, setchatLog] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [isSaving, setIsSaving] = useState(false)
    const [isLogging, setIsLogging] = useState(false)

    useEffect(()=> { //calls loadDb endpoint
        const createNewDB = async() => {
            await api.post("/new").then((response) => {
                console.log(response.data); // Parsed JSON object/array
            })
            .catch((error) => {
                console.error("Error:", error);
            });
        }
        const handleLoadDB = async() => {
            await api.get("/loadDB").then((response) => {
                console.log(response.data); // Parsed JSON object/array
                setHistory(response.data)
            })
            .catch((error) => {
                console.error("Error:", error);
            });
        }
        if (isLoading) {
            createNewDB()
            handleLoadDB()
            setIsLoading(false)
        }
    }, [])

    useEffect(()=> { //calls dumpDB endpoint
        const handleDumpDB = async () => {
            await api.post("/dumpDB", {list: history})
            .then((response) => {
                console.log("Dumping history into db", response.data); // Parsed JSON object/array
            })
            .catch((error) => {
                console.error("Error:", error);
            });
        }
        if (isSaving) {
            handleDumpDB()
            setIsSaving(false)
        }
    }, [history])

    useEffect(()=> { //calls dumpLog endpoint
        const handleDumpLog = async () => {
            await api.post("/dumpDB", {list: history})
            .then((response) => {
                console.log(response.data); 
            })
            .catch((error) => {
                console.error("Error:", error);
            });
        }
        if (isLogging) {
            handleDumpDB()
            setIsLogging(false)
        }
    }, [chatLog])

    const chat = async () => {
        await api.post("/chat", {'list': history})
        .then((response) => {
            setHistory(prev=>[...prev,response.data['list']])
            console.log("Fetching /chat API response", response.data); // Parsed JSON object/array
        })
        .catch((error) => {
            console.error("Error:", error);
        });
    }

    const handleReset = async () => {
        await api.post("/reset").then((response) => {
                console.log(response.data); 
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
    const handleChat = () => {
        const formatted_msg = {'role': 'user', 'content': msg}
        setIsSaving(true)
        setIsLogging(true)
        console.log("formatted msg", formatted_msg)
        console.log("history",history)
        setHistory([...prev, formatted_msg]
        )
        console.log("Chatting with current history...", history)
        const resp_history = chat()
        setHistory(resp_history)
        setMsg("")
        console.log(history)
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
                    {history ? <h1>Empty</h1> : history.map((msg) => {
                        return <p>{`${msg.role}: ${msg.content}`}</p>
                    })}
                </div>
            </form>
        </main>
    )
}

export default Home