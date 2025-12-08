/**
 * Truffle configuration for FlightChain blockchain layer.
 * Uses Ganache for local development.
 */

module.exports = {
    networks: {
        // Local development network (Ganache)
        development: {
            host: "127.0.0.1",
            port: 8545,
            network_id: "*", // Match any network id
            gas: 6721975,
            gasPrice: 20000000000,
        },

        // Test network configuration (for future use)
        test: {
            host: "127.0.0.1",
            port: 8545,
            network_id: "*",
        },
    },

    // Compiler configuration
    compilers: {
        solc: {
            version: "0.8.19",
            settings: {
                optimizer: {
                    enabled: true,
                    runs: 200,
                },
                evmVersion: "paris",
            },
        },
    },

    // Plugin configuration
    plugins: [],

    // Mocha testing configuration
    mocha: {
        timeout: 100000,
    },
};
