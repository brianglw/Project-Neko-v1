import ChatInput from '../components/ChatInput.jsx'
import ChatMessages from '../components/ChatMessages.jsx'

import {useState, useEffect} from 'react'

import '../App.css'

const Home = () => {

    return (
        <main>
            <ChatMessages />
            <ChatInput />
        </main>
    )
}

export default Home