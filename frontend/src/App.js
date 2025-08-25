import React, { useState, useEffect } from 'react';
import './App.css';

// Define the backend API URL. For development, this will be localhost.
// For production on Cloud Run, you'll set this to your backend's URL.
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

function App() {
  const [files, setFiles] = useState([]);
  const [activeLinks, setActiveLinks] = useState([]);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState('');

  // Fetch files and active links from the backend when the component mounts
  useEffect(() => {
    fetchFiles();
    fetchActiveLinks();
  }, []);

  const fetchFiles = async () => {
    try {
      const response = await fetch(`${API_URL}/files`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setFiles(data);
    } catch (e) {
      setError(`Failed to fetch files: ${e.message}`);
    }
  };

  const fetchActiveLinks = async () => {
    try {
      const response = await fetch(`${API_URL}/active-links`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setActiveLinks(data);
    } catch (e) {
      setError(`Failed to fetch active links: ${e.message}`);
    }
  };

  const generateLink = async (fileName) => {
    try {
      const response = await fetch(`${API_URL}/generate-signed-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ fileName: fileName, expiration: 15 }), // 15 minutes
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setNotification(`Link generated for ${fileName}: ${data.signed_url}`);
      // Auto-refresh the active links list
      fetchActiveLinks();
      // Clear the notification after a few seconds
      setTimeout(() => setNotification(''), 10000);
    } catch (e) {
      setError(`Failed to generate link: ${e.message}`);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setNotification('Copied to clipboard!');
    setTimeout(() => setNotification(''), 3000);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>GCS Signed URL Manager</h1>
      </header>
      <main className="container">
        {error && <div className="error-message">{error}</div>}
        {notification && <div className="notification-message">{notification}</div>}

        <div className="section">
          <h2>Files in Bucket</h2>
          <button onClick={fetchFiles} className="refresh-button">Refresh Files</button>
          <ul className="file-list">
            {files.length > 0 ? (
              files.map((file) => (
                <li key={file.name}>
                  <span>{file.name}</span>
                  <button onClick={() => generateLink(file.name)}>
                    Generate Sharable Link
                  </button>
                </li>
              ))
            ) : (
              <p>No files found in the bucket.</p>
            )}
          </ul>
        </div>

        <div className="section">
          <h2>Active Sharable Links</h2>
          <button onClick={fetchActiveLinks} className="refresh-button">Refresh Links</button>
          <ul className="link-list">
            {activeLinks.length > 0 ? (
              activeLinks.map((link) => (
                <li key={link.id}>
                  <strong>{link.file_name}</strong>
                  <br />
                  <small>Expires: {new Date(link.expires_at).toLocaleString()}</small>
                  <br />
                  {/* We don't display the full URL here for security, but you could */}
                  <button onClick={() => copyToClipboard(link.signed_url_hash)}>
                    Copy Link Hash
                  </button>
                </li>
              ))
            ) : (
              <p>No active links found.</p>
            )}
          </ul>
        </div>
      </main>
    </div>
  );
}

export default App;
