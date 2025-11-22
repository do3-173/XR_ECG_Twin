module.exports = {
    uiPort: process.env.NODE_RED_PORT || 1880,
    debugMaxLength: 1000,
    flowFile: '/data/flows.json',
    flowFilePretty: true,
    credentialSecret: process.env.NODE_RED_CREDENTIAL_SECRET || "a-secret-key-for-railway",
    userDir: '/data/',
    nodesDir: '/data/nodes',
    uiHost: "0.0.0.0",
    mqttReconnectTime: 15000,
    serialReconnectTime: 15000,
    socketReconnectTime: 10000,
    socketTimeout: 120000,
    tlsConfigDisableLocalFiles: false,
    debugUseColors: true,
    flowFile: 'flows.json',
    contextStorage: {
        default: {
            module: "memory"
        }
    },
    logging: {
        console: {
            level: "info",
            metrics: false,
            audit: false
        }
    },
    httpAdminRoot: '/admin',
    httpNodeRoot: '/api',
    httpNodeMiddleware: function(req,res,next) {
        res.header("Access-Control-Allow-Origin", "*");
        res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
        next();
    },
    apiMaxLength: '5mb',
    ui: { path: "ui" },
    disableEditor: false,
}
