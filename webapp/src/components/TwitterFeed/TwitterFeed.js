import './TwitterFeed.css';

const TwitterFeed = (props) => {
    const { avatar, tweets } = props;
    return (
        <div class="tweetsContainer">
            <ul id="tweetsList" class="tweetsList">        
                { tweets.map(tweet => 
                    <li>
                        <div class="tweetMainLevel">
                            <div className="avatar"> 
                                <img src={avatar} width="65px" height="65px" />
                            </div>
                            <div className="tweetBox d-f fd-c">
                                <div className="d-f jc-sb al-c tweetHead">
                                    <h3 className="primaryLight">@{ tweet.username }</h3>
                                    <p className="primaryLight">{ tweet.date } { tweet.time }</p>
                                </div>
                                <div className="tweetContent">
                                    <p className="primaryDarker">{ tweet.tweet }</p>
                                </div>
                            </div>
                        </div>
                    </li>)
                }    
            </ul>
        </div>
    )
}

export default TwitterFeed;