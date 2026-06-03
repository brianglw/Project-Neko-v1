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

    useEffect(()=> { //creates connection to an existing db, or creates new one if doesn't exist
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
                console.log(typeof response.data, response.data); // Parsed JSON object/array
                setHistory(response.data['memo'])
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

    useEffect(()=> { //updates history (short-term) and chatlog DB each chat state changes
        const handleDumpDB = async (data, filename) => {
            await api.post(`/dumpDB/${filename}`, {memo: data})
            .then((response) => {
                console.log(`Dumped ${filename} into db`, response.data); 
            })
            .catch((error) => {
                console.error("Error:", error);
            });
        }
        if (doesSaving) {
            print("Dumping history", history)
            handleDumpDB(history, "history")
            setDoesSaving(false)
        }
        if (doesLogging) {
            print("Dumping log", history)
            handleDumpDB(history.at(-1), "chatlog")
            setDoesLogging(false)
        }
    }, [history, chatLog])

    const handleReset = async () => { //clears DB records and empties chat state
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

    const handleTextChange = (e) => { //updates state from textbox value as user enters
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
        await api.post("/chat", {'memo': history})
        .then((response) => {
            setHistory(...response.data['memo'])
            setChatLog(prev => [...prev, response.data['memo'].at(-1)])
            console.log("History after reply", history)
            console.log("Chatlog after reply", chatLog)
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