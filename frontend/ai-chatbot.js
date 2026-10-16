/* =========================================================
   BUGFLOW - ADMIN AI CHATBOT
   Frontend interaction and conversation interface
   ========================================================= */

(function () {
    // Prevent the same script from initializing twice.
    if (window.bugFlowChatbotInitialized) {
        console.warn("BugFlow chatbot is already initialized.");
        return;
    }

    window.bugFlowChatbotInitialized = true;

    function initializeChatbot() {
        const chatMessages = document.getElementById("chatMessages");
        const chatForm = document.getElementById("chatForm");
        const chatInput = document.getElementById("chatInput");
        const sendButton = document.getElementById("sendButton");
        const clearChatButton = document.getElementById("clearChat");
        const chatStatus = document.getElementById("chatStatus");

        const promptButtons = document.querySelectorAll(
            ".chatbot-prompts [data-prompt]"
        );

        if (
            !chatMessages ||
            !chatForm ||
            !chatInput ||
            !sendButton ||
            !clearChatButton ||
            !chatStatus
        ) {
            console.error(
                "BugFlow chatbot: required HTML elements are missing."
            );
            return;
        }

        // FastAPI chatbot endpoint.
        const CHAT_API_URL =
            "http://127.0.0.1:8000/api/v1/chatbot/message";

        let conversation = [];
        let isSending = false;

        // -----------------------------------------------------
        // STATUS
        // -----------------------------------------------------

        function setStatus(message, type = "") {
            chatStatus.replaceChildren();

            const indicator = document.createElement("span");
            indicator.className = "status-indicator";
            indicator.setAttribute("aria-hidden", "true");

            chatStatus.append(
                indicator,
                document.createTextNode(message)
            );

            chatStatus.classList.remove("error", "success");

            if (type) {
                chatStatus.classList.add(type);
            }
        }

        // -----------------------------------------------------
        // WELCOME SCREEN
        // -----------------------------------------------------

        function showWelcome() {
            chatMessages.replaceChildren();

            const welcome = document.createElement("div");
            welcome.className = "chat-welcome";

            const iconBox = document.createElement("div");
            iconBox.className = "chat-welcome-icon";

            const icon = document.createElement("i");
            icon.className = "fa-solid fa-wand-magic-sparkles";
            icon.setAttribute("aria-hidden", "true");

            iconBox.appendChild(icon);

            const heading = document.createElement("h3");
            heading.textContent = "How can I help you today?";

            const description = document.createElement("p");
            description.textContent =
                "Ask a question about BugFlow, issue management, " +
                "user roles, priorities, or resolution assistance. " +
                "You can type your own question or choose a suggestion below.";

            welcome.append(iconBox, heading, description);
            chatMessages.appendChild(welcome);

            setStatus("Ready to connect to BugFlow AI");
        }

        // -----------------------------------------------------
        // ADD MESSAGE
        // -----------------------------------------------------

        function addMessage(message, sender) {
            const messageElement = document.createElement("div");

            messageElement.className =
                "chat-message " +
                (sender === "user" ? "user" : "assistant");

            messageElement.textContent = message;
            messageElement.setAttribute("role", "article");

            messageElement.setAttribute(
                "aria-label",
                sender === "user"
                    ? "Your message"
                    : "BugFlow assistant message"
            );

            chatMessages.appendChild(messageElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            return messageElement;
        }

        // -----------------------------------------------------
        // TYPING INDICATOR
        // -----------------------------------------------------

        function showTypingIndicator() {
            const typing = document.createElement("div");

            typing.className = "chat-typing";
            typing.setAttribute("role", "status");
            typing.setAttribute(
                "aria-label",
                "Assistant is responding"
            );

            typing.appendChild(
                document.createTextNode("Assistant is thinking ")
            );

            for (let index = 0; index < 3; index++) {
                const dot = document.createElement("span");
                dot.textContent = ".";
                typing.appendChild(dot);
            }

            chatMessages.appendChild(typing);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            return typing;
        }

        // -----------------------------------------------------
        // REQUEST BACKEND RESPONSE
        // -----------------------------------------------------

        async function requestAssistantReply(message) {
            const token = localStorage.getItem("access_token");

            if (!token) {
                throw new Error(
                    "Your login session was not found. Please sign in again."
                );
            }

            const response = await fetch(CHAT_API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + token
                },
                body: JSON.stringify({
                    message: message,
                    conversation: conversation
                })
            });

            if (!response.ok) {
                let detail = "";

                try {
                    const errorData = await response.json();
                    detail =
                        errorData.detail ||
                        errorData.message ||
                        "";
                } catch (_) {
                    // The response may not contain JSON.
                }

                if (response.status === 401) {
                    throw new Error(
                        "Your session has expired. Please sign in again."
                    );
                }

                if (response.status === 403) {
                    throw new Error(
                        detail ||
                        "Administrator access is required for this chatbot."
                    );
                }

                throw new Error(
                    detail ||
                    "Chat service error (HTTP " +
                    response.status +
                    "). Please try again."
                );
            }

            const data = await response.json();

            const reply =
                data.reply ??
                data.answer ??
                data.response ??
                data.message;

            if (typeof reply !== "string" || !reply.trim()) {
                throw new Error(
                    "The chatbot returned an empty response. Check the backend response format."
                );
            }

            return reply.trim();
        }

        // -----------------------------------------------------
        // SEND MESSAGE
        // -----------------------------------------------------

        async function sendMessage(message) {
            const cleanMessage = message.trim();

            if (!cleanMessage || isSending) {
                return;
            }

            if (cleanMessage.length > 2000) {
                setStatus(
                    "Your question must be 2,000 characters or fewer.",
                    "error"
                );
                return;
            }

            isSending = true;
            sendButton.disabled = true;
            chatInput.disabled = true;

            const welcome = chatMessages.querySelector(".chat-welcome");

            if (welcome) {
                welcome.remove();
            }

            addMessage(cleanMessage, "user");

            conversation.push({
                role: "user",
                content: cleanMessage
            });

            chatInput.value = "";
            setStatus("Processing your question...");

            const typingIndicator = showTypingIndicator();

            try {
                const reply = await requestAssistantReply(cleanMessage);

                typingIndicator.remove();

                addMessage(reply, "assistant");

                conversation.push({
                    role: "assistant",
                    content: reply
                });

                setStatus("Response received", "success");
            } catch (error) {
                typingIndicator.remove();

                addMessage(
                    error.message ||
                    "Unable to get a response. Please try again.",
                    "assistant"
                );

                setStatus("Unable to get a response", "error");

                console.error("BugFlow chatbot:", error);
            } finally {
                isSending = false;
                sendButton.disabled = false;
                chatInput.disabled = false;
                chatInput.focus();
            }
        }

        // -----------------------------------------------------
        // FORM SUBMISSION
        // Register only one handler during initialization.
        // -----------------------------------------------------

        chatForm.addEventListener("submit", function (event) {
            event.preventDefault();
            sendMessage(chatInput.value);
        });

        // -----------------------------------------------------
        // BUILT-IN QUESTION BUTTONS
        // Each click sends exactly one question.
        // -----------------------------------------------------

        promptButtons.forEach(function (button) {
            button.addEventListener("click", function (event) {
                event.preventDefault();

                const prompt = button.dataset.prompt;

                if (!prompt || isSending) {
                    return;
                }

                sendMessage(prompt);
            });
        });

        // -----------------------------------------------------
        // NEW CHAT
        // -----------------------------------------------------

        clearChatButton.addEventListener("click", function (event) {
            event.preventDefault();

            if (isSending) {
                return;
            }

            conversation = [];
            chatInput.value = "";

            showWelcome();
            chatInput.focus();
        });

        // -----------------------------------------------------
        // INITIALIZE ONCE
        // -----------------------------------------------------

        showWelcome();
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeChatbot,
            { once: true }
        );
    } else {
        initializeChatbot();
    }
})();