import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

const CustomizedDot = (props) => {
    const { cx, cy, payload } = props;
    if (payload.tweeted) {
      const colour = payload.compound > 0 ? '#c2ffc0' : payload.compound < 0 ? '#ffbaba' :'grey';
      return (
        <svg x={cx - 10} y={cy - 10} width={64} height={64} fill={colour} viewBox="0 0 1024 1024">
          <path d="M273.4 26.4a110 110 0 0 1-32.2 8.8a56 56 0 0 0 24.6-31a107 107 0 0 1-35.6 13.6A56.1 56.1 0 0 0 134.6 69A159 159 0 0 1 19 10.4a56 56 0 0 0 17.4 74.9a60 60 0 0 1-25.4-7a56 56 0 0 0 45 55.6a60 60 0 0 1-25.4 1a56 56 0 0 0 52.4 39a112 112 0 0 1-83 23a159 159 0 0 0 245.4-141.5a108 108 0 0 0 28-29z" />        
        </svg>
      );
    }
};

const Chart = (props) => {
    const { data } = props;

    return (
        <LineChart
          width={750}
          height={250}
          data={data}
        >
          <XAxis stroke="white" dataKey="date" />
          <YAxis stroke="white" dataKey="price" />
          <Tooltip fill={'#38bdf8'} />
          <Line type="monotone" dataKey="price" stroke="white" dot={<CustomizedDot />} />
        </LineChart>
    );
}

export default Chart;