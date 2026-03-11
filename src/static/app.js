document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const authStatus = document.getElementById("auth-status");
  const userMenuBtn = document.getElementById("user-menu-btn");
  const loginModal = document.getElementById("login-modal");
  const loginForm = document.getElementById("login-form");
  const closeModalBtn = document.getElementById("close-modal-btn");
  const logoutBtn = document.getElementById("logout-btn");

  let adminToken = sessionStorage.getItem("adminToken") || null;
  let adminUsername = sessionStorage.getItem("adminUsername") || null;

  function getAuthHeaders() {
    if (!adminToken) {
      return {};
    }
    return { "X-Admin-Token": adminToken };
  }

  function setMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.classList.remove("hidden");

    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  function updateAuthView() {
    if (adminToken && adminUsername) {
      authStatus.textContent = `Teacher: ${adminUsername}`;
    } else {
      authStatus.textContent = "Student view";
    }
  }

  async function validateStoredSession() {
    if (!adminToken) {
      updateAuthView();
      return;
    }

    try {
      const response = await fetch("/auth/status", {
        headers: getAuthHeaders(),
      });
      const result = await response.json();

      if (!result.authenticated) {
        sessionStorage.removeItem("adminToken");
        sessionStorage.removeItem("adminUsername");
        adminToken = null;
        adminUsername = null;
      } else {
        adminUsername = result.username;
        sessionStorage.setItem("adminUsername", adminUsername);
      }
    } catch (error) {
      sessionStorage.removeItem("adminToken");
      sessionStorage.removeItem("adminUsername");
      adminToken = null;
      adminUsername = null;
    }

    updateAuthView();
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      activitySelect.innerHTML =
        '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map((email) => {
                    const deleteButton = adminToken
                      ? `<button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button>`
                      : "";
                    return `<li><span class="participant-email">${email}</span>${deleteButton}</li>`;
                  })
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    if (!adminToken) {
      setMessage("Teacher login is required to unregister students.", "error");
      return;
    }

    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
          headers: getAuthHeaders(),
        }
      );

      const result = await response.json();

      if (response.ok) {
        setMessage(result.message, "success");

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        setMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      setMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!adminToken) {
      setMessage("Teacher login is required to register students.", "error");
      return;
    }

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
          headers: getAuthHeaders(),
        }
      );

      const result = await response.json();

      if (response.ok) {
        setMessage(result.message, "success");
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        setMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      setMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  userMenuBtn.addEventListener("click", () => {
    loginModal.classList.remove("hidden");
  });

  closeModalBtn.addEventListener("click", () => {
    loginModal.classList.add("hidden");
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const result = await response.json();

      if (!response.ok) {
        setMessage(result.detail || "Login failed", "error");
        return;
      }

      adminToken = result.token;
      adminUsername = result.username;
      sessionStorage.setItem("adminToken", adminToken);
      sessionStorage.setItem("adminUsername", adminUsername);
      updateAuthView();
      setMessage(`Logged in as ${adminUsername}`, "success");
      loginForm.reset();
      loginModal.classList.add("hidden");
      fetchActivities();
    } catch (error) {
      setMessage("Login failed. Please try again.", "error");
    }
  });

  logoutBtn.addEventListener("click", async () => {
    if (!adminToken) {
      setMessage("You are not currently logged in.", "info");
      return;
    }

    try {
      await fetch("/auth/logout", {
        method: "POST",
        headers: getAuthHeaders(),
      });
    } catch (error) {
      console.error("Logout request failed:", error);
    }

    adminToken = null;
    adminUsername = null;
    sessionStorage.removeItem("adminToken");
    sessionStorage.removeItem("adminUsername");
    updateAuthView();
    setMessage("Logged out", "success");
    fetchActivities();
  });

  // Initialize app
  validateStoredSession().then(fetchActivities);
});
