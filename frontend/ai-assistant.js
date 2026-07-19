(function () {
  const API_BASES = [
    window.STOCKSENSEI_API_BASE,
    "http://127.0.0.1:5001",
    "http://localhost:5001",
    "http://127.0.0.1:5000",
    "http://localhost:5000"
  ].filter(Boolean);

  async function askBackend(question) {
    let lastError = "Backend unavailable";

    for (const base of API_BASES) {
      try {
        const response = await fetch(base + "/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question })
        });
        const data = await response.json();
        if (response.ok) return data;
        lastError = data.error || response.statusText;
      } catch (error) {
        lastError = error.message;
      }
    }

    throw new Error(lastError);
  }

  function createPanel() {
    if (document.querySelector(".global-ai-panel")) return;

    const panel = document.createElement("section");
    panel.className = "global-ai-panel";
    panel.setAttribute("aria-label", "Ask StockSensei");
    panel.innerHTML = `
      <div class="global-ai-top">
        <div>
          <h2>Ask StockSensei</h2>
          <p>Ask a stock learning question and get an educational AI response.</p>
        </div>
        <span class="global-ai-badge">Education only</span>
      </div>
      <form class="global-ai-form">
        <input type="text" maxlength="900" placeholder="Ask about confidence, risk, charts, or market terms...">
        <button type="submit">Ask AI</button>
      </form>
      <div class="global-ai-answer"></div>
    `;

    const footer = document.querySelector(".site-footer");
    if (footer) {
      footer.parentNode.insertBefore(panel, footer);
    } else {
      document.body.insertBefore(panel, document.body.lastElementChild);
    }

    const form = panel.querySelector("form");
    const input = panel.querySelector("input");
    const button = panel.querySelector("button");
    const answer = panel.querySelector(".global-ai-answer");

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const question = input.value.trim();

      if (!question) {
        answer.textContent = "Type a question first.";
        answer.classList.add("visible");
        return;
      }

      button.disabled = true;
      button.textContent = "Thinking...";
      answer.textContent = "Generating an educational answer...";
      answer.classList.add("visible");

      try {
        const data = await askBackend(question);
        answer.textContent = data.answer || "No answer returned.";
      } catch (error) {
        answer.textContent = error.message + " Make sure the backend is running and OPENAI_API_KEY is set.";
      } finally {
        button.disabled = false;
        button.textContent = "Ask AI";
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", createPanel);
  } else {
    createPanel();
  }
})();
