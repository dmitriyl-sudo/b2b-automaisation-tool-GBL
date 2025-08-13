import { useState } from 'react';
import axios from 'axios';

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('/login', new URLSearchParams({
        username,
        password
      }));
      const token = res.data.access_token;
      localStorage.setItem('token', token);
      const me = await axios.get('/me', {
        headers: { Authorization: `Bearer ${token}` }
      });
      onLogin({ ...me.data, token });
    } catch (err) {
      alert('Login failed');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-6 max-w-sm mx-auto space-y-4 bg-white shadow-md rounded-md">
      <h2 className="text-xl font-bold text-center">🔐 Login to System</h2>
      <input
        className="border p-2 w-full rounded focus:outline-none focus:ring focus:border-blue-400"
        placeholder="Username"
        value={username}
        onChange={e => setUsername(e.target.value)}
      />
      <input
        className="border p-2 w-full rounded focus:outline-none focus:ring focus:border-blue-400"
        type="password"
        placeholder="Password"
        value={password}
        onChange={e => setPassword(e.target.value)}
      />
      <button
        type="submit"
        className="bg-blue-600 hover:bg-blue-700 transition text-white px-4 py-2 rounded w-full"
      >
        Log in
      </button>
    </form>
  );
}
