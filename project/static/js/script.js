const byId = (id) => document.getElementById(id);
const apiCache = new Map();

async function fetchJsonCached(url, ttlMs = 180000) {
  const now = Date.now();
  const cached = apiCache.get(url);
  if (cached && now - cached.time < ttlMs) {
    return cached.data;
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  const data = await res.json();
  apiCache.set(url, { time: now, data });
  return data;
}

function showToast(message) {
  const container = byId("toastContainer");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 2600);
}

function setupNavbar() {
  const burger = byId("hamburger");
  const nav = byId("navMenu");
  if (!burger || !nav) return;
  burger.addEventListener("click", () => nav.classList.toggle("active"));
}

function setupTopbarScrollEffect() {
  const topbar = document.querySelector(".topbar");
  if (!topbar) return;
  let ticking = false;

  window.addEventListener(
    "scroll",
    () => {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(() => {
        const currentY = window.scrollY || 0;
        const awayFromTop = currentY > 10;
        if (awayFromTop) {
          topbar.classList.add("scrolled-up-dark");
        } else {
          topbar.classList.remove("scrolled-up-dark");
        }
        ticking = false;
      });
    },
    { passive: true }
  );
}

function setupReveal() {
  const targets = document.querySelectorAll(".reveal");
  if (!targets.length) return;
  targets.forEach((el, index) => {
    el.style.transitionDelay = `${Math.min(index * 60, 420)}ms`;
  });
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("active");
        }
      });
    },
    { threshold: 0.15 }
  );
  targets.forEach((el) => observer.observe(el));
}

function setupSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener("click", (e) => {
      const target = document.querySelector(link.getAttribute("href"));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

function setupLogin() {
  const loginForm = byId("loginForm");
  if (!loginForm) return;

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = byId("username")?.value.trim();
    const password = byId("password")?.value.trim();

    if (!username || !password) {
      showToast("Login failed. Please fill all fields.");
      return;
    }

    try {
      const res = await fetch("/auth/login-register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();

      if (!res.ok || !data.success) {
        showToast(data.message || "Login failed.");
        return;
      }

      showToast(data.message || "Login successful");
      setTimeout(() => {
        window.location.href = "/dashboard";
      }, 800);
    } catch (_err) {
      showToast("Unable to login right now.");
    }
  });
}

function setupAuthControls() {
  const logoutBtn = byId("logoutBtn");
  const userBadge = byId("userBadge");
  const loginLinks = document.querySelectorAll(".login-link");

  fetch("/session-status")
    .then((r) => r.json())
    .then((data) => {
      if (data.logged_in) {
        loginLinks.forEach((el) => el.classList.add("hidden"));
        if (logoutBtn) logoutBtn.classList.remove("hidden");
        if (userBadge) {
          userBadge.textContent = `Hi, ${data.username}`;
          userBadge.classList.remove("hidden");
        }
      } else {
        loginLinks.forEach((el) => el.classList.remove("hidden"));
        if (logoutBtn) logoutBtn.classList.add("hidden");
        if (userBadge) userBadge.classList.add("hidden");
      }
    })
    .catch(() => {
      if (logoutBtn) logoutBtn.classList.add("hidden");
    });

  logoutBtn?.addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      const res = await fetch("/auth/logout", { method: "POST" });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast("Logged out");
        setTimeout(() => {
          window.location.href = "/login";
        }, 600);
      }
    } catch (_err) {
      showToast("Logout failed.");
    }
  });
}

function createResultCard(title, bodyHtml) {
  const card = document.createElement("article");
  card.className = "card glass";
  card.innerHTML = `<h3>${title}</h3>${bodyHtml}`;
  return card;
}

function mapSkillsToInterests(skills) {
  const s = skills.map((x) => x.toLowerCase());
  const interests = [];
  if (s.some((x) => ["python", "machine learning", "sql", "data"].includes(x))) interests.push("data");
  if (s.some((x) => ["html", "css", "javascript", "react"].includes(x))) interests.push("frontend");
  if (s.some((x) => ["figma", "design", "ux", "ui"].includes(x))) interests.push("design");
  if (s.some((x) => ["cloud", "aws", "azure"].includes(x))) interests.push("cloud");
  if (s.some((x) => ["docker", "kubernetes", "linux", "ci/cd"].includes(x))) interests.push("automation");
  if (!interests.length) interests.push("frontend");
  return interests;
}

function setupDashboard() {
  const analyzeBtn = byId("analyzeBtn");
  const uploadBtn = byId("uploadBtn");
  const quizBtn = byId("quizBtn");
  const historyBtn = byId("historyBtn");
  const savedBtn = byId("savedBtn");
  const clearResultsBtn = byId("clearResultsBtn");
  const results = byId("resultsContainer");
  const statsGrid = byId("statsGrid");
  const toolOutput = byId("toolOutput");
  if (!analyzeBtn || !uploadBtn || !results) return;
  const resumeInput = byId("resumeInput");
  const toolRole = byId("toolRole");
  const toolLanguage = byId("toolLanguage");
  const toolCompany = byId("toolCompany");
  const toolPortfolioUrl = byId("toolPortfolioUrl");
  const toolReminderText = byId("toolReminderText");
  const toolReminderDue = byId("toolReminderDue");
  const toolResumeContent = byId("toolResumeContent");

  const buildFallbackResumeContent = () => {
    const role = (toolRole?.value || "General Candidate").trim();
    const skills = (byId("skillsInput")?.value || "Problem Solving, Communication")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
      .join(", ");
    return `Candidate Resume\nTarget Role: ${role}\n\nSUMMARY\nMotivated candidate with strong execution skills.\n\nSKILLS\n${skills}\n\nEXPERIENCE\n- Delivered project outcomes with measurable impact.\n\nEDUCATION\nBachelor's Degree`;
  };

  const renderToolCards = (cards = []) => {
    if (!toolOutput) return;
    toolOutput.innerHTML = "";
    cards.forEach((c) => {
      toolOutput.appendChild(createResultCard(c.title, c.body));
    });
  };

  toolOutput?.addEventListener("click", async (e) => {
    const btn = e.target.closest("button[data-tool-action]");
    if (!btn) return;
    const action = btn.dataset.toolAction;
    try {
      if (action === "track-application") {
        const payload = {
          job_id: btn.dataset.jobId,
          title: btn.dataset.title,
          company: btn.dataset.company || "",
          status: "Applied",
        };
        const r = await fetch("/applications", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.error || "Unable to track application");
        showToast("Application saved");
      } else if (action === "set-app-status") {
        const r = await fetch("/applications/status", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            job_id: btn.dataset.jobId,
            status: btn.dataset.status,
          }),
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.error || "Unable to update status");
        showToast("Application status updated");
      } else if (action === "complete-reminder") {
        const r = await fetch("/reminders", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            id: btn.dataset.reminderId,
            completed: true,
          }),
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.error || "Unable to complete reminder");
        showToast("Reminder marked complete");
      }
    } catch (err) {
      if (String(err.message).includes("Authentication required")) {
        window.location.href = "/login";
        return;
      }
      showToast(err.message || "Action failed");
    }
  });

  const renderDashboardStats = async () => {
    if (!statsGrid) return;
    try {
      const res = await fetch("/dashboard-stats");
      const data = await res.json();
      if (!res.ok) return;
      statsGrid.innerHTML = "";
      statsGrid.appendChild(createResultCard("Analyses", `<p>${data.analyses}</p>`));
      statsGrid.appendChild(createResultCard("Resume Uploads", `<p>${data.resumes}</p>`));
      statsGrid.appendChild(createResultCard("Saved Careers", `<p>${data.bookmarks}</p>`));
    } catch (_err) {
      // keep silent for fast load
    }
  };
  renderDashboardStats();

  analyzeBtn.addEventListener("click", async () => {
    const raw = byId("skillsInput")?.value || "";
    const skills = raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    if (!skills.length) {
      showToast("Please enter at least one skill.");
      return;
    }

    try {
      const res = await fetch("/analyze-skills", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ skills }),
      });
      const data = await res.json();

      if (!res.ok) throw new Error(data.error || "Analysis failed");

      results.innerHTML = "";
      const primaryCard = createResultCard(
        "Top Career Match",
        `<p><strong>Career:</strong> ${data.career}</p>
         <p><strong>Match Score:</strong> ${data.match_score}%</p>
         <p><strong>Missing Skills:</strong> ${(data.missing_skills || []).join(", ") || "None"}</p>`
      );
      primaryCard.classList.add("full-span");
      results.appendChild(primaryCard);

      const options = Array.isArray(data.top_matches) ? data.top_matches : [];
      if (options.length) {
        options.forEach((opt) => {
          results.appendChild(
            createResultCard(
              opt.career,
              `<p><strong>Match:</strong> ${opt.match_score}%</p>
               <p><strong>Salary:</strong> ${opt.salary || "N/A"}</p>
               <p><strong>Demand:</strong> ${opt.demand_level || "N/A"}</p>
               <p><strong>Missing:</strong> ${(opt.missing_skills || []).join(", ") || "None"}</p>`
            )
          );
        });
      } else if (Array.isArray(data.alternatives) && data.alternatives.length) {
        results.appendChild(
          createResultCard(
            "More Options",
            `<p>${data.alternatives.join(", ")}</p>`
          )
        );
      }
      showToast("Analysis completed");
      renderDashboardStats();
    } catch (err) {
      if (String(err.message).includes("Authentication required")) {
        window.location.href = "/login";
        return;
      }
      showToast(err.message || "Analysis failed");
    }
  });

  const uploadResumeFile = async () => {
    const file = resumeInput?.files?.[0];
    if (!file) {
      showToast("Please choose a PDF resume first.");
      return;
    }

    const formData = new FormData();
    formData.append("resume", file);

    try {
      const res = await fetch("/upload-resume", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Upload failed");

      const skills = data.extracted_skills?.length
        ? data.extracted_skills.join(", ")
        : "No known skills detected.";
      const assessments = Array.isArray(data.job_assessment) ? data.job_assessment : [];
      const portfolioRows = Array.isArray(data.portfolio_assessment) ? data.portfolio_assessment : [];
      const links = Array.isArray(data.detected_links) ? data.detected_links : [];
      const assessmentHtml = assessments.length
        ? assessments
            .map(
              (row) =>
                `<li><strong>${row.career}</strong> - ${row.fit_score}% fit - ${
                  row.acceptable ? "Acceptable" : "Not yet acceptable"
                }</li>`
            )
            .join("")
        : "<li>No job match data available.</li>";
      const portfolioHtml = portfolioRows.length
        ? portfolioRows
            .map(
              (row) =>
                `<li><strong>${row.score}/100</strong> - <a href="${row.portfolio_url}" target="_blank">Portfolio Link</a></li>`
            )
            .join("")
        : "<li>No portfolio link detected in resume.</li>";
      const linksHtml = links.length
        ? links.map((u) => `<li><a href="${u}" target="_blank">${u}</a></li>`).join("")
        : "<li>No links detected.</li>";

      const card = createResultCard(
        "Resume Analysis",
        `<p><strong>Extracted Skills:</strong> ${skills}</p>
         <p><strong>Parse Method:</strong> ${data.parse_method || "unknown"}</p><p><strong>Resume Job Acceptance Check:</strong></p>
         <ul>${assessmentHtml}</ul>
         <p><strong>Detected Links:</strong></p>
         <ul>${linksHtml}</ul>
         <p><strong>Portfolio Auto-Analysis:</strong></p>
         <ul>${portfolioHtml}</ul>`
      );
      results.prepend(card);
      showToast("Resume uploaded successfully");
      renderDashboardStats();
    } catch (err) {
      if (String(err.message).includes("Authentication required")) {
        window.location.href = "/login";
        return;
      }
      showToast(err.message || "Upload failed");
    }
  };

  uploadBtn.addEventListener("click", uploadResumeFile);
  resumeInput?.addEventListener("change", () => {
    if (resumeInput.files?.length) uploadResumeFile();
  });

  quizBtn?.addEventListener("click", async () => {
    const raw = byId("skillsInput")?.value || "";
    const skills = raw.split(",").map((s) => s.trim()).filter(Boolean);
    const interests = mapSkillsToInterests(skills);
    try {
      const res = await fetch("/career-quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interests }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Quiz failed");
      results.prepend(
        createResultCard(
          "Quick Quiz Suggestion",
          `<p><strong>Career:</strong> ${data.career}</p>
           <p><strong>Alternatives:</strong> ${(data.alternatives || []).join(", ")}</p>`
        )
      );
      showToast("Quiz suggestion ready");
    } catch (err) {
      if (String(err.message).includes("Authentication required")) {
        window.location.href = "/login";
        return;
      }
      showToast(err.message || "Quiz failed");
    }
  });

  historyBtn?.addEventListener("click", async () => {
    try {
      const res = await fetch("/analysis-history");
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Unable to load history");

      results.innerHTML = "";
      if (!data.length) {
        results.appendChild(
          createResultCard("History", "<p>No analysis history yet.</p>")
        );
        return;
      }

      data.forEach((entry) => {
        const card = createResultCard(
          `History - ${entry.result.career}`,
          `<p><strong>Skills:</strong> ${(entry.skills || []).join(", ")}</p>
           <p><strong>Match:</strong> ${entry.result.match_score}%</p>
           <p><strong>Missing:</strong> ${(entry.result.missing_skills || []).join(", ")}</p>`
        );
        results.appendChild(card);
      });
      showToast("History loaded");
    } catch (err) {
      if (String(err.message).includes("Authentication required")) {
        window.location.href = "/login";
        return;
      }
      showToast(err.message || "Unable to load history");
    }
  });

  savedBtn?.addEventListener("click", async () => {
    try {
      const res = await fetch("/bookmarks");
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Unable to load saved careers");
      results.innerHTML = "";
      if (!data.length) {
        results.appendChild(createResultCard("Saved Careers", "<p>No saved careers yet.</p>"));
      } else {
        data.forEach((item) => {
          results.appendChild(createResultCard("Saved Career", `<p>${item.career_title}</p>`));
        });
      }
      showToast("Saved careers loaded");
      renderDashboardStats();
    } catch (err) {
      if (String(err.message).includes("Authentication required")) {
        window.location.href = "/login";
        return;
      }
      showToast(err.message || "Unable to load saved careers");
    }
  });

  clearResultsBtn?.addEventListener("click", () => {
    results.innerHTML = "";
    showToast("Results cleared");
  });

  byId("toolJobsBtn")?.addEventListener("click", async () => {
    try {
      const role = encodeURIComponent((toolRole?.value || "").trim());
      const language = encodeURIComponent((toolLanguage?.value || "").trim());
      const r = await fetch(`/jobs?limit=18&role=${role}&language=${language}`);
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Unable to load jobs");
      const cards = (data || []).map((j) => ({
        title: `${j.title}`,
        body: `<p><strong>${j.company}</strong> - ${j.location}</p>
               <p><strong>Job Language:</strong> ${j.job_language || "English"}</p>
               <p><strong>Tech:</strong> ${(j.programming_languages || []).join(", ") || "N/A"}</p>
               <p><a href="${j.apply_link}" target="_blank">Apply Link</a></p>
               <button class="btn-secondary" data-tool-action="track-application" data-job-id="${j.id}" data-title="${j.title}" data-company="${j.company}">Track Application</button>`,
      }));
      renderToolCards(cards.length ? cards : [{ title: "Jobs", body: "<p>No jobs matched your filters.</p>" }]);
    } catch (err) {
      if (String(err.message).includes("Authentication required")) {
        window.location.href = "/login";
        return;
      }
      showToast(err.message || "Unable to load jobs");
    }
  });

  byId("toolAppsBtn")?.addEventListener("click", async () => {
    try {
      const r = await fetch("/applications");
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Unable to load applications");
      const cards = data.length
        ? data.map((a) => ({
            title: `${a.title} (${a.status})`,
            body: `<p>${a.company || "Unknown Company"}</p><p>Updated: ${a.updated_at || "-"}</p>
                   <div class="action-row">
                     <button class="btn-secondary" data-tool-action="set-app-status" data-job-id="${a.job_id}" data-status="Interviewing">Mark Interviewing</button>
                     <button class="btn-secondary" data-tool-action="set-app-status" data-job-id="${a.job_id}" data-status="Rejected">Mark Rejected</button>
                     <button class="btn-secondary" data-tool-action="set-app-status" data-job-id="${a.job_id}" data-status="Offer">Mark Offer</button>
                   </div>`,
          }))
        : [{ title: "Applications", body: "<p>No applications yet.</p>" }];
      renderToolCards(cards);
    } catch (err) {
      if (String(err.message).includes("Authentication required")) {
        window.location.href = "/login";
        return;
      }
      showToast(err.message || "Unable to load applications");
    }
  });

  byId("toolCoverBtn")?.addEventListener("click", async () => {
    try {
      const r = await fetch("/generate-cover-letter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: byId("rbName")?.value || "Candidate",
          role: toolRole?.value || "Software Engineer",
          company: toolCompany?.value || "Target Company",
          summary: byId("rbSummary")?.value || "I bring strong technical and collaboration skills.",
          skills: (byId("rbSkills")?.value || "").split(",").map((s) => s.trim()).filter(Boolean),
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Unable to generate cover letter");
      renderToolCards([{ title: "Cover Letter", body: `<pre class="resume-preview">${data.cover_letter}</pre>` }]);
    } catch (err) {
      showToast(err.message || "Unable to generate cover letter");
    }
  });

  byId("toolInterviewBtn")?.addEventListener("click", async () => {
    try {
      const role = toolRole?.value || "Software Engineer";
      const qRes = await fetch("/mock-interview/questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
      });
      const qData = await qRes.json();
      if (!qRes.ok) throw new Error(qData.error || "Unable to load interview questions");

      const answers = (qData.questions || []).map((q, i) => `For question ${i + 1}, I solved a real project challenge with measurable impact of 25%.`);
      const fRes = await fetch("/mock-interview/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers }),
      });
      const fData = await fRes.json();
      if (!fRes.ok) throw new Error("Unable to score interview");

      const cards = (qData.questions || []).map((q, idx) => ({
        title: `Q${idx + 1}`,
        body: `<p>${q}</p><p><strong>Score:</strong> ${(fData.feedback?.[idx]?.score) || 0}</p>`,
      }));
      renderToolCards(cards);
    } catch (err) {
      showToast(err.message || "Unable to run interview");
    }
  });

  byId("toolRoadmapBtn")?.addEventListener("click", async () => {
    try {
      const missingSkills = (byId("skillsInput")?.value || "").split(",").map((s) => s.trim()).filter(Boolean);
      const r = await fetch("/skill-roadmap", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ missing_skills: missingSkills }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Unable to build roadmap");
      const cards = (data.roadmap || []).map((w) => ({
        title: `Week ${w.week}: ${w.focus_skill}`,
        body: `<p>${(w.tasks || []).join(" | ")}</p>`,
      }));
      renderToolCards(cards);
    } catch (err) {
      showToast(err.message || "Unable to build roadmap");
    }
  });

  byId("toolPortfolioBtn")?.addEventListener("click", async () => {
    try {
      const r = await fetch("/portfolio-analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          portfolio_url: toolPortfolioUrl?.value || "",
          role: toolRole?.value || "Software Engineer",
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Unable to analyze portfolio");
      renderToolCards([
        {
          title: `Portfolio Score: ${data.score}/100`,
          body: `<p>${(data.feedback || []).join("<br/>")}</p>`,
        },
      ]);
    } catch (err) {
      showToast(err.message || "Unable to analyze portfolio");
    }
  });

  byId("toolSaveVersionBtn")?.addEventListener("click", async () => {
    try {
      const content = byId("rbPreview")?.textContent || "";
      const resumeContent = (toolResumeContent?.value || content || "").trim() || buildFallbackResumeContent();
      const r = await fetch("/resume-versions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          version_name: `${toolRole?.value || "General"} Resume`,
          role: toolRole?.value || "General",
          content: resumeContent,
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Unable to save version");
      showToast("Resume version saved");
    } catch (err) {
      showToast(err.message || "Unable to save version");
    }
  });

  byId("toolVersionsBtn")?.addEventListener("click", async () => {
    try {
      const r = await fetch("/resume-versions");
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Unable to load versions");
      const cards = data.length
        ? data.map((v) => ({ title: v.version_name, body: `<p>Role: ${v.role}</p><p>Created: ${v.created_at}</p>` }))
        : [{ title: "Resume Versions", body: "<p>No versions saved yet.</p>" }];
      renderToolCards(cards);
    } catch (err) {
      showToast(err.message || "Unable to load versions");
    }
  });

  byId("toolExportPdfBtn")?.addEventListener("click", async () => {
    try {
      const r = await fetch("/export-resume-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: "careercompass_resume",
          content: (toolResumeContent?.value || byId("rbPreview")?.textContent || "").trim() || buildFallbackResumeContent(),
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Unable to export PDF");
      showToast(`PDF exported: ${data.file_path}`);
    } catch (err) {
      showToast(err.message || "Unable to export PDF");
    }
  });

  byId("toolAdminBtn")?.addEventListener("click", async () => {
    try {
      const r = await fetch("/admin-analytics");
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Unable to load analytics");
      renderToolCards([
        { title: "Total Analyses", body: `<p>${data.total_analyses}</p>` },
        { title: "Total Resumes", body: `<p>${data.total_resumes}</p>` },
        { title: "Total Applications", body: `<p>${data.total_applications}</p>` },
        {
          title: "Top Careers",
          body: `<p>${(data.top_careers || []).map((x) => `${x.career} (${x.count})`).join(", ") || "No data"}</p>`,
        },
      ]);
    } catch (err) {
      showToast(err.message || "Unable to load analytics");
    }
  });

  byId("toolReminderBtn")?.addEventListener("click", async () => {
    try {
      const r = await fetch("/reminders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: toolReminderText?.value || "", due_date: toolReminderDue?.value || "" }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Unable to add reminder");
      showToast("Reminder added");
    } catch (err) {
      showToast(err.message || "Unable to add reminder");
    }
  });

  byId("toolReminderListBtn")?.addEventListener("click", async () => {
    try {
      const r = await fetch("/reminders");
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Unable to load reminders");
      const cards = data.length
        ? data.map((x) => ({
            title: x.text,
            body: `<p>Due: ${x.due_date || "-"}</p><p>Done: ${x.completed ? "Yes" : "No"}</p>
                   ${
                     x.completed
                       ? ""
                       : `<button class="btn-secondary" data-tool-action="complete-reminder" data-reminder-id="${x.id}">Mark Complete</button>`
                   }`,
          }))
        : [{ title: "Reminders", body: "<p>No reminders yet.</p>" }];
      renderToolCards(cards);
    } catch (err) {
      showToast(err.message || "Unable to load reminders");
    }
  });

  const params = new URLSearchParams(window.location.search);
  if (params.get("tool") === "1") {
    setTimeout(() => byId("toolJobsBtn")?.click(), 120);
  }
}

function setupCareers() {
  const cardsEl = byId("careerCards");
  if (!cardsEl) return;
  const searchInput = byId("careerSearch");

  const modal = byId("careerModal");
  const closeModal = byId("closeModal");

  const modalTitle = byId("modalTitle");
  const modalSalary = byId("modalSalary");
  const modalSkills = byId("modalSkills");
  const modalRoadmap = byId("modalRoadmap");

  const openModal = (career) => {
    modalTitle.textContent = career.title;
    modalSalary.textContent = career.salary;

    modalSkills.innerHTML = "";
    career.required_skills.forEach((skill) => {
      const li = document.createElement("li");
      li.textContent = skill;
      modalSkills.appendChild(li);
    });

    modalRoadmap.innerHTML = "";
    career.roadmap.forEach((step) => {
      const li = document.createElement("li");
      li.textContent = step;
      modalRoadmap.appendChild(li);
    });

    modal.classList.remove("hidden");
  };

  closeModal?.addEventListener("click", () => modal.classList.add("hidden"));
  modal?.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.add("hidden");
  });

  fetch("/careers")
    .then((r) => r.json())
    .then((careers) => {
      cardsEl.innerHTML = "";

      const render = (filterText = "") => {
        const query = filterText.trim().toLowerCase();
        const filtered = careers.filter((career) => {
          if (!query) return true;
          return (
            career.title.toLowerCase().includes(query) ||
            career.required_skills.some((skill) => skill.toLowerCase().includes(query))
          );
        });

        cardsEl.innerHTML = "";
        filtered.forEach((career) => {
          const card = document.createElement("article");
          card.className = "card glass careers-card";
          card.innerHTML = `<h3>${career.title}</h3><p>Click to view salary, skills, and roadmap.</p><button class="btn-secondary save-career-btn">Save</button>`;
          const saveBtn = card.querySelector(".save-career-btn");
          saveBtn?.addEventListener("click", async (e) => {
            e.stopPropagation();
            try {
              const res = await fetch("/bookmarks", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ career_title: career.title }),
              });
              const data = await res.json();
              if (!res.ok) throw new Error(data.error || "Save failed");
              showToast(data.message || "Saved");
            } catch (err) {
              if (String(err.message).includes("Authentication required")) {
                window.location.href = "/login";
                return;
              }
              showToast(err.message || "Save failed");
            }
          });
          card.addEventListener("click", () => openModal(career));
          cardsEl.appendChild(card);
        });

        if (!filtered.length) {
          cardsEl.appendChild(
            createResultCard("No Match", "<p>Try a different title or skill keyword.</p>")
          );
        }
      };

      render();
      searchInput?.addEventListener("input", (e) => render(e.target.value));
    })
    .catch(() => showToast("Unable to load careers right now."));
}

function setupPopularCareersHome() {
  const popularGrid = byId("popularCareerGrid");
  if (!popularGrid) return;

  fetchJsonCached("/careers", 300000)
    .then((careers) => {
      popularGrid.innerHTML = "";
      careers.slice(0, 4).forEach((career) => {
        const card = document.createElement("article");
        card.className = "card glass popular-card";
        const demand = career.demand_level || "Growing";
        card.innerHTML = `
          <h3>${career.title}</h3>
          <div class="career-meta">
            <span class="badge">${demand} Demand</span>
            <span class="badge">${career.salary}</span>
          </div>
          <p>${career.required_skills.slice(0, 3).join(", ")}</p>
          <a class="btn-inline" href="/careers-page">View Roadmap</a>
        `;
        popularGrid.appendChild(card);
      });
    })
    .catch(() => {
      showToast("Unable to load popular careers right now.");
    });
}

function setupPublicStatsHome() {
  const grid = byId("publicStatsGrid");
  if (!grid) return;
  fetchJsonCached("/careers", 300000)
    .then((careers) => {
      grid.innerHTML = "";
      grid.appendChild(createResultCard("Career Tracks", `<p>${careers.length}</p>`));
      const veryHigh = careers.filter((c) => (c.demand_level || "").toLowerCase().includes("very")).length;
      grid.appendChild(createResultCard("Very High Demand Roles", `<p>${veryHigh}</p>`));
      grid.appendChild(createResultCard("Top Skills Indexed", "<p>25+</p>"));
    });
}

function setupJobsPreviewHome() {
  const grid = byId("jobsPreviewGrid");
  if (!grid) return;
  fetchJsonCached("/jobs-preview", 120000)
    .then((jobs) => {
      grid.innerHTML = "";
      (jobs || []).forEach((job) => {
        grid.appendChild(
          createResultCard(
            job.title || "Job Role",
            `<p><strong>${job.company || "Company"}</strong> - ${job.location || "Location"}</p>
             <p><a href="${job.apply_link || "#"}" target="_blank">Open Apply Link</a></p>`
          )
        );
      });
      if (!jobs || !jobs.length) {
        grid.appendChild(createResultCard("Jobs Feed", "<p>No jobs available right now.</p>"));
      }
    })
    .catch(() => {
      showToast("Unable to load jobs preview.");
    });
}

function setupResumeBuilder() {
  const previewBtn = byId("rbPreviewBtn");
  const scoreBtn = byId("rbScoreBtn");
  const downloadBtn = byId("rbDownloadBtn");
  const templateSelect = byId("rbTemplate");
  const applyTemplateBtn = byId("rbApplyTemplateBtn");
  const bgSelect = byId("rbBgTheme");
  const applyBgBtn = byId("rbApplyBgBtn");
  const previewEl = byId("rbPreview");
  const scoreEl = byId("rbScore");
  const tipsEl = byId("rbTips");
  const roleSelect = byId("rbRole");
  if (!previewBtn || !downloadBtn || !previewEl || !roleSelect) return;

  const resumeTemplates = {
    fresher: {
      role: "Web Developer",
      summary: "Entry-level developer with strong foundations in HTML, CSS, JavaScript, and problem solving. Built multiple projects and collaborated in hackathons to deliver user-friendly products.",
      skills: "HTML, CSS, JavaScript, React, Git, REST APIs",
      experience: "Built a student portal frontend using React and integrated APIs.\nCreated responsive landing pages with accessibility best practices.\nContributed to team project in hackathon and delivered before deadline.",
      projects: "CareerCompass AI - Built sections, API integration, and responsive UI.\nPortfolio Website - Personal site with project showcase and contact form.",
      education: "B.Tech in Computer Science, 2026",
    },
    software: {
      role: "Backend Developer",
      summary: "Software engineer focused on backend systems, API development, and reliability. Experienced in designing scalable services with clear architecture and monitoring.",
      skills: "Python, Flask, FastAPI, SQL, PostgreSQL, Docker, CI/CD",
      experience: "Designed REST APIs for internal workflow automation and cut manual processing by 45%.\nOptimized database queries and reduced API response time by 35%.\nImplemented CI pipeline with automated tests and deployment gates.",
      projects: "Order Service API - Role-based auth, pagination, caching, and audit logs.\nRealtime Notification Engine - WebSocket-based event streaming for dashboards.",
      education: "B.E. in Information Science, 2024",
    },
    data: {
      role: "Data Scientist",
      summary: "Data scientist skilled in turning business questions into measurable models and dashboards. Comfortable with data cleaning, feature engineering, model evaluation, and stakeholder communication.",
      skills: "Python, SQL, Pandas, NumPy, Scikit-Learn, TensorFlow, Power BI",
      experience: "Built churn prediction model that improved retention campaign targeting by 22%.\nCreated ETL pipeline and automated daily analytics reports.\nDeveloped KPI dashboard used by product and growth teams.",
      projects: "Customer Churn Predictor - End-to-end pipeline with model monitoring.\nSales Forecasting Model - Time-series forecasting with scenario analysis.",
      education: "M.Sc. in Data Science, 2025",
    },
    designer: {
      role: "UI/UX Designer",
      summary: "UI/UX designer focused on clean interfaces, user research, and high-conversion flows. Experienced in wireframing, prototyping, usability testing, and design system consistency.",
      skills: "Figma, Wireframing, Prototyping, User Research, Design Systems, Accessibility",
      experience: "Redesigned onboarding flow and improved completion rate by 28%.\nRan usability tests and translated findings into product improvements.\nBuilt reusable design components to speed up delivery across teams.",
      projects: "Fintech App Redesign - End-to-end case study with measurable UX improvements.\nE-Commerce Design System - Tokens, components, and accessibility patterns.",
      education: "B.Des in Interaction Design, 2023",
    },
  };

  const applyResumeBackground = () => {
    const selected = (bgSelect?.value || "classic").trim();
    const allowed = new Set(["classic", "sky", "mint", "sunset"]);
    const theme = allowed.has(selected) ? selected : "classic";
    previewEl.className = `resume-preview resume-shell rb-theme-${theme}`;
  };

  let careers = [];
  fetchJsonCached("/careers", 300000)
    .then((data) => {
      careers = Array.isArray(data) ? data : [];
      roleSelect.innerHTML = `<option value="">Target Role (Select from careers)</option>`;
      careers.forEach((c) => {
        const option = document.createElement("option");
        option.value = c.title;
        option.textContent = c.title;
        roleSelect.appendChild(option);
      });
    })
    .catch(() => {
      roleSelect.innerHTML = `<option value="">Target Role (Type manually in summary)</option>`;
    });

  const readForm = () => {
    const name = byId("rbName")?.value.trim() || "Your Name";
    const email = byId("rbEmail")?.value.trim() || "your.email@example.com";
    const phone = byId("rbPhone")?.value.trim() || "Phone Number";
    const location = byId("rbLocation")?.value.trim() || "Location";
    const linkedin = byId("rbLinkedin")?.value.trim();
    const github = byId("rbGithub")?.value.trim();
    const role = roleSelect?.value?.trim() || "Target Role";
    const summary = byId("rbSummary")?.value.trim() || "Add your professional summary.";
    const skillsRaw = byId("rbSkills")?.value.trim() || "";
    const skillList = skillsRaw
      ? skillsRaw.split(",").map((s) => s.trim()).filter(Boolean)
      : [];
    const expRaw = byId("rbExperience")?.value.trim() || "";
    const expLines = (expRaw
      ? expRaw.split("\n").map((line) => line.trim()).filter(Boolean)
      : ["Add your experience points here."]);
    const projectsRaw = byId("rbProjects")?.value.trim() || "";
    const projectLines = projectsRaw
      ? projectsRaw.split("\n").map((line) => line.trim()).filter(Boolean)
      : [];
    const education = byId("rbEducation")?.value.trim() || "Add your education details.";

    return {
      name, email, phone, location, linkedin, github, role, summary, skillList, expLines, projectLines, education
    };
  };

  const escapeHtml = (value) =>
    String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const getRoleRequirements = (role) => {
    const row = careers.find((c) => c.title === role);
    return row ? row.required_skills || [] : [];
  };

  const computeAtsScore = (data) => {
    const required = getRoleRequirements(data.role);
    const userSkillsLower = new Set(data.skillList.map((s) => s.toLowerCase()));
    const matched = required.filter((s) => userSkillsLower.has(s.toLowerCase()));

    const summaryWords = data.summary.split(/\s+/).filter(Boolean).length;
    const hasContact = Boolean(data.name && data.email && data.phone);
    const hasLinks = Boolean(data.linkedin || data.github);
    const quantifiedBullets = data.expLines.filter((line) => /\d/.test(line)).length;

    let score = 0;
    const tips = [];

    if (hasContact) score += 15; else tips.push("Add complete contact details (name, email, phone).");
    if (summaryWords >= 35 && summaryWords <= 120) score += 15; else tips.push("Keep summary between 35 and 120 words.");

    const skillScore = required.length ? Math.round((matched.length / required.length) * 35) : 18;
    score += skillScore;
    if (required.length && matched.length < Math.ceil(required.length * 0.6)) {
      const missing = required.filter((s) => !userSkillsLower.has(s.toLowerCase())).slice(0, 5);
      tips.push(`Add role keywords: ${missing.join(", ")}.`);
    }

    if (quantifiedBullets >= 2) score += 20; else tips.push("Use quantified achievements (numbers, %, revenue, users).");
    if (hasLinks) score += 5; else tips.push("Add LinkedIn or portfolio/GitHub link.");
    if (data.projectLines.length >= 1) score += 10; else tips.push("Add at least one project relevant to the target role.");

    score = Math.min(100, score);
    return { score, tips, matched, required };
  };

  const buildResumeText = () => {
    const data = readForm();
    const ats = computeAtsScore(data);
    const prioritizedSkills = data.skillList.slice().sort((a, b) => {
      const aMatch = ats.matched.some((m) => m.toLowerCase() === a.toLowerCase()) ? 1 : 0;
      const bMatch = ats.matched.some((m) => m.toLowerCase() === b.toLowerCase()) ? 1 : 0;
      return bMatch - aMatch;
    });

    const links = [data.linkedin, data.github].filter(Boolean).join(" | ");
    const contactLine = `${data.email} | ${data.phone} | ${data.location}${links ? ` | ${links}` : ""}`;
    const skillsBlock = prioritizedSkills.length ? prioritizedSkills.join(", ") : "Add your skills here.";
    const projectsBlock = data.projectLines.length
      ? data.projectLines.map((line) => `- ${line}`).join("\n")
      : "- Add one project with impact and technologies used.";

    return `${data.name}
${contactLine}
Target Role: ${data.role}

SUMMARY
${data.summary}

SKILLS
${skillsBlock}

EXPERIENCE
${data.expLines.map((line) => `- ${line}`).join("\n")}

PROJECTS
${projectsBlock}

EDUCATION
${data.education}
`;
  };

  const renderResumePreview = () => {
    applyResumeBackground();
    const data = readForm();
    const ats = computeAtsScore(data);
    const links = [data.linkedin, data.github].filter(Boolean).join(" | ");
    const skillsHtml = (data.skillList.length ? data.skillList : ["Add your skills here."])
      .map((skill) => {
        const matched = ats.matched.some((m) => m.toLowerCase() === skill.toLowerCase());
        return `<span class="resume-chip ${matched ? "matched" : ""}">${escapeHtml(skill)}</span>`;
      })
      .join("");
    const expHtml = data.expLines.map((line) => `<li>${escapeHtml(line)}</li>`).join("");
    const projectsHtml = (data.projectLines.length ? data.projectLines : ["Add one project with impact and technologies used."])
      .map((line) => `<li>${escapeHtml(line)}</li>`)
      .join("");

    previewEl.innerHTML = `
      <div class="resume-head">
        <h2>${escapeHtml(data.name)}</h2>
        <p>${escapeHtml(data.email)} | ${escapeHtml(data.phone)} | ${escapeHtml(data.location)}</p>
        ${links ? `<p>${escapeHtml(links)}</p>` : ""}
      </div>
      <div class="resume-section">
        <h4>Target Role</h4>
        <p>${escapeHtml(data.role)}</p>
      </div>
      <div class="resume-section">
        <h4>Summary</h4>
        <p>${escapeHtml(data.summary)}</p>
      </div>
      <div class="resume-section">
        <h4>Skills</h4>
        <div class="resume-chip-wrap">${skillsHtml}</div>
      </div>
      <div class="resume-section">
        <h4>Experience</h4>
        <ul>${expHtml}</ul>
      </div>
      <div class="resume-section">
        <h4>Projects</h4>
        <ul>${projectsHtml}</ul>
      </div>
      <div class="resume-section">
        <h4>Education</h4>
        <p>${escapeHtml(data.education)}</p>
      </div>
    `;
  };

  const renderScore = () => {
    const data = readForm();
    const ats = computeAtsScore(data);
    if (scoreEl) scoreEl.textContent = `ATS Score: ${ats.score}/100`;
    if (tipsEl) {
      tipsEl.innerHTML = "";
      ats.tips.slice(0, 4).forEach((tip) => {
        const li = document.createElement("li");
        li.textContent = tip;
        tipsEl.appendChild(li);
      });
      if (!ats.tips.length) {
        const li = document.createElement("li");
        li.textContent = "Great. Resume is well aligned for the selected role.";
        tipsEl.appendChild(li);
      }
    }
  };

  applyTemplateBtn?.addEventListener("click", () => {
    const key = templateSelect?.value;
    if (!key || !resumeTemplates[key]) {
      showToast("Select a template first.");
      return;
    }
    const tpl = resumeTemplates[key];
    if (tpl.role) roleSelect.value = tpl.role;
    if (tpl.summary) byId("rbSummary").value = tpl.summary;
    if (tpl.skills) byId("rbSkills").value = tpl.skills;
    if (tpl.experience) byId("rbExperience").value = tpl.experience;
    if (tpl.projects) byId("rbProjects").value = tpl.projects;
    if (tpl.education) byId("rbEducation").value = tpl.education;
    renderResumePreview();
    renderScore();
    showToast("Template applied");
  });

  applyBgBtn?.addEventListener("click", () => {
    applyResumeBackground();
    showToast("Background updated");
  });

  bgSelect?.addEventListener("change", applyResumeBackground);
  applyResumeBackground();

  previewBtn.addEventListener("click", () => {
    renderResumePreview();
    renderScore();
    showToast("Resume preview generated");
  });

  scoreBtn?.addEventListener("click", () => {
    renderScore();
    showToast("ATS score calculated");
  });

  downloadBtn.addEventListener("click", async () => {
    const content = buildResumeText();
    renderResumePreview();
    renderScore();
    try {
      const filename = (byId("rbName")?.value || "careercompass_resume")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_+|_+$/g, "") || "careercompass_resume";

      const res = await fetch("/export-resume-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename,
          content,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Unable to export PDF");
      if (data.download_url) {
        const link = document.createElement("a");
        link.href = data.download_url;
        link.download = `${filename}.pdf`;
        document.body.appendChild(link);
        link.click();
        link.remove();
      }
      showToast("Resume PDF downloaded");
    } catch (err) {
      showToast(err.message || "PDF export failed");
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupAuthControls();
  setupNavbar();
  setupTopbarScrollEffect();
  setupReveal();
  setupSmoothScroll();
  setupLogin();
  setupDashboard();
  setupCareers();
  setupPopularCareersHome();
  setupPublicStatsHome();
  setupJobsPreviewHome();
  setupResumeBuilder();
  window.showToast = showToast;
});
