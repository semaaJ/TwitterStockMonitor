
import React, { useState } from 'react';
import User from '../components/User/User';
import TwitterFeed from '../components/TwitterFeed/TwitterFeed';
import Chart from '../components/Chart/Chart';
import { FaHome } from 'react-icons/fa';
import './UserPage.css';

const UserPage = (props) => {
    const { user, mentions, tweets, historical, setSelected } = props;
    const [company, setCompany] = useState(Object.keys(mentions)[0]);

    // Last 100 days
    const chartData = historical[company].date.slice(historical[company].date.length - 100).reduce((acc, curr, i) => {
        let tweeted = false;
        let compound = 0;
        mentions[company].forEach(mention => {
            if (mention.date === curr && mention.companies.includes(company)) {
                tweeted = true;
                compound = mention.compound
            }
        })
        acc.push({ date: curr, price: historical[company].close[historical[company].date.length - 100 + i], tweeted: tweeted, compound: compound });
        return acc;
    }, [])

    return (
        <div className="w-100 d-f j-c-sb">
            <div className="left d-f fd-c ">
                <div className="d-f">
                    <User user={user} />
                    <div className="d-f fd-c jc-sa h-100">
                        <div className="d-f jc-c al-c icon" onClick={() => setSelected(null) }>
                            <FaHome color="white" size={26} />
                        </div>
                    </div>
                </div>

                <div className="card">
                    <h2>Companies Mentioned</h2>
                    <div className="d-f jc-sb f-w">
                        {   
                            Object.keys(mentions).map(val => 
                                <h3 
                                    onClick={() => setCompany(val)} 
                                    className={ val === company ? 'company selected' : 'company'}
                                >
                                    { val }
                                </h3>
                            )
                        }
                    </div>
                </div>

                <div className="card">
                    <Chart data={chartData}/>
                </div>

                <div className="d-f fd-c card mentions">
                    <h2>Tweets</h2>
                    { mentions[company].map(mention => {
                        let colour;
                        let symbol = "-";

                        if (mention.compound > 0) {
                            colour = "pos";
                            symbol = "✓"
                        } else if (mention.compound < 0) {
                            colour = "neg";
                            symbol = "✗";
                        }

                        return (
                            <div className="d-f jc-sb al-c">
                                <p className={`${colour} companyMention`}>"{ mention.tweet }"</p>
                                <p className="neg">{ mention.neg.toFixed(3) }</p>
                                <p>{ mention.neu.toFixed(3) }</p>
                                <p className="pos">{ mention.pos.toFixed(3) }</p>
                                <p>{ mention.compound.toFixed(3) }</p>
                                <h3 className={colour}>{ symbol }</h3>
                            </div>
                            )
                        })
                    }
                </div>
            </div>
            <TwitterFeed tweets={tweets} avatar={user.avatar} />
        </div>
    )
}

export default UserPage;