const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(endpoint, options = {}) {
    let response;

    try {
        response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    } catch {
        throw new Error(
            "Cannot connect to the backend. Check that FastAPI is running."
        );
    }

    const contentType = response.headers.get("content-type");
    const data = contentType?.includes("application/json")
        ? await response.json()
        : await response.text();

    if (!response.ok) {
        const message =
            typeof data === "object" && data !== null
                ? data.detail || JSON.stringify(data)
                : data || `Request failed: ${response.status}`;


        if (response.status === 401) {
            throw new Error("Your session is invalid or expired. Please log in again.");
        }

        throw new Error(message);


    }

    return data;
}

export const api = {
    health: () => request("/health"),

    login: ({ email, password }) => {
        const formData = new URLSearchParams();
        formData.set("username", email);
        formData.set("password", password);


        return request("/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: formData,
        });


    },
    getBookings: (token) =>
        request("/bookings", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        }),

    checkSlots: () => request("/tools/check-slots"),

    pendingApprovals: (token) =>
        request("/approvals/pending", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        }),

    approveBooking: (approvalId, token) =>
        request(`/approvals/${approvalId}/approve`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
            },
        }),

    rejectApproval: (approvalId, token) =>
        request(`/approvals/${approvalId}/reject`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
            },
        }),
    
    
    chatWithAgent: (message, conversationHistory = []) =>
        request("/agent/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                message,
                conversation_history: conversationHistory,
            }),
        }),


    
};
