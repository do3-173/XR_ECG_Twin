FROM nodered/node-red:latest

# Switch to root to install packages
USER root

# Create necessary directories and set permissions
RUN mkdir -p /data/.npm && \
    chown -R node-red:node-red /data

# Switch back to node-red user
USER node-red

# Set working directory
WORKDIR /usr/src/node-red

# Install Node-RED Dashboard using the node-red user
RUN npm install --prefix /data node-red-dashboard

# Copy flows and settings
COPY --chown=node-red:node-red flows.json /data/flows.json
COPY --chown=node-red:node-red settings.js /data/settings.js

# Expose Node-RED port
EXPOSE 1880

# Start Node-RED with proper user directory
CMD ["node-red", "--userDir", "/data"]
