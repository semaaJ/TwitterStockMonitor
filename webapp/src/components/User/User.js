import './User.css';

const User = (props) => {
    const { user, setSelected, width } = props;
    const onUserClick = () => setSelected(user);
    
    return (
        <div className="outer" style={width !== null ? { width: width } : {}} onClick={() => onUserClick()}>
            <div className="d-f al-c user">
                <img className="userAvi" src={user.avatar} width="120px" height="120px" />
                <div className="userInfo">
                    <div className="d-f jc-sb al-c">
                        <h1>{ user.name }</h1>
                        <h3 className="primaryLight">{ user.verified ? '✓' : '' }</h3>
                    </div>
                    <div className="d-f jc-sb al-c">
                        <h3>@{ user.username }</h3>
                        <h3>{ Number(user.followers).toLocaleString() }</h3>
                    </div>
                    <p>{ user.bio }</p>
                </div>
            </div>
        </div>
        
    )
}

export default User;