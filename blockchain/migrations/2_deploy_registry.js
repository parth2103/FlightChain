const FlightEventRegistry = artifacts.require("FlightEventRegistry");

module.exports = async function (deployer, network, accounts) {
    // Deploy the FlightEventRegistry contract
    await deployer.deploy(FlightEventRegistry);

    const registry = await FlightEventRegistry.deployed();

    console.log("=".repeat(60));
    console.log("FlightEventRegistry deployed successfully!");
    console.log("Contract Address:", registry.address);
    console.log("Owner:", accounts[0]);
    console.log("Network:", network);
    console.log("=".repeat(60));

    // Log for backend configuration
    console.log("\nAdd this to your backend .env file:");
    console.log(`CONTRACT_ADDRESS=${registry.address}`);
};
