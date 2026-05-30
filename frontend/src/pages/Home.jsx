import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import SendIcon from '@mui/icons-material/Send';
import {useState, useEffect} from 'react'
import api from '../services/api.js'

const Home = () => {
    const [history, setHistory] = useState([])
    const [newMsg, setNewMsg] = useState([])

    useEffect(async ()=> { //calls loadDb endpoint
        response = await api.get("/loadDB")
        setHistory(response)
    }, [])

    useEffect(async ()=> { //calls dumpDB endpoint
        response = await api.post("/dumpDB")
        setHistory(response)
    }, [history])

    useEffect(async ()=> { //calls dumpLog endpoint
        response = await api.post("/dumpLog")
    }, [newMsg])
    
    return (
        <main>
            <form>
                <TextField
                    fullWidth
                    id="filled-multiline-static"
                    label="Chat"
                    multiline
                    rows={4}
                    placeholder='Type your message here'
                    variant="filled"
                />
                <Button variant="contained">
                    <SendIcon />
                </Button>
            </form>
        </main>
    )
}

export default Home