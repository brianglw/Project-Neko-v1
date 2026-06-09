import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import HighlightOffIcon from '@mui/icons-material/HighlightOff';
import SendIcon from '@mui/icons-material/Send';

import {useChatContext} from '../contexts/ChatContext.jsx'

const ChatInput = () => {
    const {handleSubmit, handleTextChange, handleKeyEvent, msg, handleClearChat} = useChatContext()
    return (
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
                onKeyDown={handleKeyEvent}
                value={msg}
            />
            <Button type='submit' variant="contained" >
                <SendIcon />
            </Button>
            <Button onClick={handleClearChat} variant="contained">
                <HighlightOffIcon />
            </Button>
        </form>
    )
}

export default ChatInput