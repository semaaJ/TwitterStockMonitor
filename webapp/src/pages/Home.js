import User from '../components/User/User';
import './Home.css'

const Home = (props) => {
    const { users, setSelected } = props;
    return (
        
        <div className="d-f fd-c">
            <h1>Twitter Users</h1>
            <div className="usersContainer">
                { users !== undefined && Object.keys(users).map(user => <User width="600px" setSelected={setSelected} user={users[user]} />) }
            </div>
        </div>
    )
}

export default Home;