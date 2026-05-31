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

    useEffect(()=> { //calls loadDb endpoint
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
            handleLoadDB()
            setIsLoading(false)
        }
    }, [])

    useEffect(()=> { //calls dumpDB endpoint
        const handleDumpDB = async () => {
            await api.post("/dumpDB", {list: history})
            .then((response) => {
                console.log(response.data); // Parsed JSON object/array
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

    useEffect(async ()=> { //calls dumpLog endpoint
        const handleDumpLog = async () => {
            await api.post("/dumpDB", {list: history})
            .then((response) => {
                console.log(response.data); // Parsed JSON object/array
            })
            .catch((error) => {
                console.error("Error:", error);
            });
        }
        if (isSaving) {
            handleDumpDB()
            setIsSaving(false)
        }
    }, [chatLog])

    const handleTextChange = (e) => {
        e.preventDefault()
        setMsg(e.target.value)
        console.log(msg)
    }

    const handleSubmit = (e) => {
        e.preventDefault()
        const formatted_msg = {'role': 'user', 'content': msg}
        setIsSaving(true)
        setHistory((prev) => {
            return [...prev, formatted_msg]
        })
        console.log(history)
        setMsg("")
        console.log(formatted_msg)
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
                {history.map((msg) => {
                    return <p>{`${msg.role}: ${msg.content}`}</p>
                })}
            </form>
        </main>
    )
}

export default Home