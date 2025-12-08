const FlightEventRegistry = artifacts.require("FlightEventRegistry");

contract("FlightEventRegistry", (accounts) => {
    const owner = accounts[0];
    const backend = accounts[1];
    const unauthorized = accounts[2];

    let registry;

    beforeEach(async () => {
        registry = await FlightEventRegistry.new({ from: owner });
    });

    describe("Deployment", () => {
        it("should set the deployer as owner", async () => {
            const contractOwner = await registry.owner();
            assert.equal(contractOwner, owner, "Owner should be the deployer");
        });

        it("should set the deployer as initial authorized backend", async () => {
            const authorizedBackend = await registry.authorizedBackend();
            assert.equal(authorizedBackend, owner, "Initial authorized backend should be owner");
        });

        it("should start with zero events", async () => {
            const totalEvents = await registry.getTotalEvents();
            assert.equal(totalEvents.toNumber(), 0, "Should start with zero events");
        });
    });

    describe("Backend Authorization", () => {
        it("should allow owner to authorize a backend", async () => {
            await registry.authorizeBackend(backend, { from: owner });
            const authorizedBackend = await registry.authorizedBackend();
            assert.equal(authorizedBackend, backend, "Backend should be authorized");
        });

        it("should emit BackendAuthorized event", async () => {
            const result = await registry.authorizeBackend(backend, { from: owner });
            assert.equal(result.logs[0].event, "BackendAuthorized");
            assert.equal(result.logs[0].args.backend, backend);
        });

        it("should reject authorization from non-owner", async () => {
            try {
                await registry.authorizeBackend(backend, { from: unauthorized });
                assert.fail("Should have thrown an error");
            } catch (error) {
                assert(error.message.includes("Only owner"), "Should reject non-owner");
            }
        });
    });

    describe("Event Recording", () => {
        const flightId = "UA123";
        const eventType = "DEPARTURE";
        const timestamp = Math.floor(Date.now() / 1000);
        const actor = "AIRLINE";
        const dataHash = web3.utils.keccak256("test-payload");

        it("should record an event successfully", async () => {
            const result = await registry.recordEvent(
                flightId,
                eventType,
                timestamp,
                actor,
                dataHash,
                { from: owner }
            );

            assert.equal(result.logs[0].event, "EventRecorded");

            const eventCount = await registry.getTotalEvents();
            assert.equal(eventCount.toNumber(), 1, "Should have one event");
        });

        it("should store event data correctly", async () => {
            await registry.recordEvent(flightId, eventType, timestamp, actor, dataHash, { from: owner });

            const event = await registry.getEvent(0);
            assert.equal(event.flightId, flightId);
            assert.equal(event.eventType, eventType);
            assert.equal(event.timestamp.toNumber(), timestamp);
            assert.equal(event.actor, actor);
            assert.equal(event.dataHash, dataHash);
        });

        it("should track events by flight ID", async () => {
            await registry.recordEvent(flightId, eventType, timestamp, actor, dataHash, { from: owner });

            const eventCount = await registry.getFlightEventCount(flightId);
            assert.equal(eventCount.toNumber(), 1);

            const indices = await registry.getFlightEventIndices(flightId);
            assert.equal(indices.length, 1);
            assert.equal(indices[0].toNumber(), 0);
        });

        it("should prevent duplicate hashes", async () => {
            await registry.recordEvent(flightId, eventType, timestamp, actor, dataHash, { from: owner });

            try {
                await registry.recordEvent(flightId, eventType, timestamp, actor, dataHash, { from: owner });
                assert.fail("Should have thrown an error");
            } catch (error) {
                assert(error.message.includes("already exists"), "Should reject duplicate hash");
            }
        });

        it("should reject recording from unauthorized address", async () => {
            try {
                await registry.recordEvent(flightId, eventType, timestamp, actor, dataHash, { from: unauthorized });
                assert.fail("Should have thrown an error");
            } catch (error) {
                assert(error.message.includes("Not authorized"), "Should reject unauthorized");
            }
        });

        it("should allow authorized backend to record events", async () => {
            await registry.authorizeBackend(backend, { from: owner });

            const result = await registry.recordEvent(
                flightId,
                eventType,
                timestamp,
                actor,
                dataHash,
                { from: backend }
            );

            assert.equal(result.logs[0].event, "EventRecorded");
        });
    });

    describe("Hash Verification", () => {
        it("should verify existing hash", async () => {
            const dataHash = web3.utils.keccak256("test-payload");
            await registry.recordEvent("UA123", "DEPARTURE", Date.now(), "SYSTEM", dataHash, { from: owner });

            const exists = await registry.verifyHash(dataHash);
            assert.equal(exists, true, "Hash should exist");
        });

        it("should return false for non-existent hash", async () => {
            const fakeHash = web3.utils.keccak256("fake-payload");
            const exists = await registry.verifyHash(fakeHash);
            assert.equal(exists, false, "Hash should not exist");
        });
    });

    describe("Multiple Events", () => {
        it("should handle multiple events for same flight", async () => {
            const events = [
                { type: "SCHEDULED", actor: "SYSTEM" },
                { type: "CHECK_IN_OPEN", actor: "AIRLINE" },
                { type: "BOARDING", actor: "GATE_AGENT" },
                { type: "DEPARTURE", actor: "ATC" },
                { type: "ARRIVAL", actor: "ATC" },
            ];

            for (let i = 0; i < events.length; i++) {
                const hash = web3.utils.keccak256(`payload-${i}`);
                await registry.recordEvent(
                    "UA123",
                    events[i].type,
                    Date.now() + i * 1000,
                    events[i].actor,
                    hash,
                    { from: owner }
                );
            }

            const eventCount = await registry.getFlightEventCount("UA123");
            assert.equal(eventCount.toNumber(), 5, "Should have 5 events");
        });

        it("should retrieve flight events in range", async () => {
            // Record 5 events
            for (let i = 0; i < 5; i++) {
                const hash = web3.utils.keccak256(`payload-${i}`);
                await registry.recordEvent("UA123", `EVENT_${i}`, Date.now() + i, "SYSTEM", hash, { from: owner });
            }

            // Get events 1-3
            const flightEvents = await registry.getFlightEvents("UA123", 1, 2);
            assert.equal(flightEvents.length, 2, "Should return 2 events");
            assert.equal(flightEvents[0].eventType, "EVENT_1");
            assert.equal(flightEvents[1].eventType, "EVENT_2");
        });
    });
});
