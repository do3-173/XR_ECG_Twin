FROM nodered/node-red:latest

# Install Node-RED Dashboard
RUN npm install node-red-dashboard

# Copy flows
COPY flows.json /data/flows.json
COPY settings.js /data/settings.js

# Expose Node-RED port
EXPOSE 1880

CMD ["npm", "start", "--cache", "/data/.npm", "--", "--userDir", "/data"]
