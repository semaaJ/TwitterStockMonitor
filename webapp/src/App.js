import React, { useState, useEffect } from 'react';
import Loader from './components/Loader/Loader';
import Home from './pages/Home';
import UserPage from './pages/UserPage';
import './App.css';

const URL = "http://127.0.0.1:5000";

function App() {
  const [selected, setSelected] = useState(null);
  const [state, setState] = useState(null)
  
  useEffect(() => {
    fetch(URL, { headers: { 'Access-Control-Allow-Origin': '*' }})
      .then(r => r.json())
      .then(d => setState(d));
  }, []);
  
  if (selected !== null) {
    return (
      <div className="App">
        { state !== null && 
          <UserPage 
            user={selected}
            setSelected={setSelected}
            mentions={state.mentions[selected.username]}
            tweets={state.tweets[selected.username]}
            historical={state.historical}
          /> 
        }
      </div>
    )
  }

  if (state !== null) {
    return (
      <div className="App">
        { state !== null &&
            <div className="d-f fd-c h-100 jc-c al-c">
              <Home 
                users={state.users}
                setSelected={setSelected}
              /> 
            </div>
        }
      </div>
    )
  }

  return (
    <div className="App">
      <div className="d-f h-100 jc-c al-c">
        <Loader />
      </div>
    </div>
  );
}

export default App;
