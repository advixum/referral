// Created with create-react-app (https://github.com/facebook/create-react-app)
import { 
  MemoryRouter as Router, Routes, Route, useNavigate ,
} from "react-router-dom"
import { useState, useEffect } from "react"
import axios from "axios"
import "./App.css"

const backendURL = "https://advixum.freemyip.com:3333" 
// "http://127.0.0.1:8000" "https://advixum.freemyip.com:3333"

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/verify" element={<Verify />} />
        <Route path="/main" element={<Main />} /> 
      </Routes>
    </Router>
  )
}

function Login() {
  const navigate = useNavigate()
  const token = localStorage.getItem("token")
  const [inputPhone, setInputPhone] = useState("")
  const [message, setMessage] = useState("")
  const [isButtonDisabled, setIsButtonDisabled] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setIsButtonDisabled(true)
    try {
      setMessage("Sending code...")
      const response = await axios.post(
        `${backendURL}/api/login/`, 
        { phone: inputPhone },
      )
      const { phone, code } = response.data
      localStorage.setItem("phone", phone)
      localStorage.setItem("code", code)
      navigate("/verify")
    } catch (error) {
      setIsButtonDisabled(false)
      setMessage(error.response.data.message)
      console.error("Error during login:", error)
    }
  }

  useEffect(() => {
    if (token) {
      navigate("/main")
    }
  }, [token, navigate])

  return (
    <div>
      <h2>Login</h2>
      {message && (
        <p>{message.charAt(0).toUpperCase() + message.slice(1)}</p>
      )}
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputPhone}
          onChange={(event) => setInputPhone(event.target.value)}
          placeholder="Enter text"
        />
        <button type="submit" disabled={isButtonDisabled}>Submit</button>
      </form>
    </div>
  )
}

function Verify() {
  const navigate = useNavigate()
  const [inputCode, setInputCode] = useState("")
  const storedPhone = localStorage.getItem("phone")
  const storedCode = localStorage.getItem("code")
  const [count, setCount] = useState("")
  const [message, setMessage] = useState("")
  const [isButtonDisabled, setIsButtonDisabled] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setIsButtonDisabled(true)
    try {
      const response = await axios.post(
        `${backendURL}/api/verify/`, 
        { phone: storedPhone, code: storedCode, verify: inputCode },
      )
      localStorage.setItem("token", response.data.token)
      setInputCode("")
      setMessage(response.data.message)
      let countdown = 3
      if (response.status === 200 || response.status === 201) {
        const intervalId = setInterval(() => {
          setCount(`Redirect to Main page in ${countdown}...`)
          countdown--
          if (countdown < 0) {
            clearInterval(intervalId)
            navigate("/main")
          }
        }, 1000)
      }
    } catch (error) {
      setIsButtonDisabled(false)
      setMessage(error.response.data.message)
      console.error("Error during verify:", error)
    }
  }

  useEffect(() => {
    if (!storedPhone || !storedCode) {
      navigate("/")
    }
  }, [storedPhone, storedCode, navigate])

  return (
    <div>
      <h2>Verify</h2>
      <p>Code from SMS: {storedCode}</p>
      {message && (
        <p>{message.charAt(0).toUpperCase() + message.slice(1)}</p>
      )}
      {count && (
        <p>{count.charAt(0).toUpperCase() + count.slice(1)}</p>
      )}
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputCode}
          onChange={(event) => setInputCode(event.target.value)}
          placeholder="Enter text"
        />
        <button type="submit" disabled={isButtonDisabled}>Accept</button>
      </form>
    </div>
  )
}

function Main() {
  const navigate = useNavigate()
  const [fromDB, setFromDB] = useState([])
  const [ref, setRef] = useState("")
  const [invited, setInvited] = useState("")
  const token = localStorage.getItem("token")
  const [inputRef, setInputRef] = useState("")
  const [message, setMessage] = useState("")
  const [isButtonDisabled, setIsButtonDisabled] = useState(false)

  const handleLogout = async () => {
    localStorage.removeItem("token")
    navigate("/")
  }

  const handleList = async () => {
    try {
      const auth = {"Authorization": `Token ${token}`}
      const response = await axios.get(
        `${backendURL}/api/data/`, { headers: auth },
      )
      setRef(response.data.ref)
      setInvited(response.data.invited)
      setFromDB(response.data.users)
    } catch (error) {
      console.error(error)
      if (error.response.status === 401) {
        handleLogout()
      }
      setMessage(error.response.data.message)
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setIsButtonDisabled(true)
    try {
      const auth = {"Authorization": `Token ${token}`}
      const response = await axios.post(
        `${backendURL}/api/data/`, 
        { ref_code: inputRef }, { headers: auth },
      )
      setInputRef("")
      setInvited(response.data.invited)
      setMessage(response.data.message)
    } catch (error) {
      setIsButtonDisabled(false)
      console.error(error)
      if (error.response.status === 401) {
        handleLogout()
      }
      setInputRef("")
      setMessage(error.response.data.message)
    }
  }

  useEffect(() => {
    handleList()
    // eslint-disable-next-line
  }, [])

  return (
    <div>
      <h2>Main</h2>
      <button className="logout-button" onClick={handleLogout}>Logout</button>
      {message && (
        <p>Message: {message.charAt(0).toUpperCase() + message.slice(1)}</p>
      )}
      <p>Your referral code: {ref}</p>
      <p>Registed referral code: {invited}</p>
      {invited === "" && (
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={inputRef}
            onChange={(event) => setInputRef(event.target.value)}
            placeholder="Enter text"
          />
          <button type="submit" disabled={isButtonDisabled}>Submit</button>
        </form>
      )}
      <p>Users invited by you:</p>
      {fromDB.length === 0 ? (
        <ul>
          <li>You haven"t invited any user yet.</li>
        </ul>
      ) : (
        <ul>
          {fromDB.map((entry, index) => (
            <li key={index}>{entry}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default App
