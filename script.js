const careerRoles = [
  {
    role: "Frontend Developer",
    skills: ["html", "css", "javascript", "uiux", "git"],
    nextSkills: ["React", "TypeScript", "Tailwind CSS", "API Integration"]
  },
  {
    role: "WordPress Developer",
    skills: ["html", "css", "javascript", "php", "wordpress", "woocommerce"],
    nextSkills: ["Custom Plugin Development", "Theme Development", "WooCommerce Hooks", "Security Optimization"]
  },
  {
    role: "Backend Developer",
    skills: ["php", "sql", "api", "git"],
    nextSkills: ["Laravel", "Node.js", "REST API", "Database Design"]
  },
  {
    role: "Data Analyst",
    skills: ["python", "sql"],
    nextSkills: ["Pandas", "Power BI", "Data Visualization", "Statistics"]
  },
  {
    role: "AI / Machine Learning Developer",
    skills: ["python", "sql", "machine-learning"],
    nextSkills: ["Scikit-learn", "TensorFlow", "Model Evaluation", "Streamlit"]
  }
];

function matchCareer() {
  const selectedSkills = Array.from(document.querySelectorAll("input[type='checkbox']:checked"))
    .map(input => input.value);

  const resultBox = document.getElementById("result");

  if (selectedSkills.length === 0) {
    resultBox.classList.remove("hidden");
    resultBox.innerHTML = `
      <h2>Please select at least one skill</h2>
      <p>Choose your current skills to generate a career match.</p>
    `;
    return;
  }

  let bestMatch = null;
  let highestScore = 0;

  careerRoles.forEach(career => {
    const matchedSkills = career.skills.filter(skill => selectedSkills.includes(skill));
    const score = Math.round((matchedSkills.length / career.skills.length) * 100);

    if (score > highestScore) {
      highestScore = score;
      bestMatch = {
        ...career,
        matchedSkills,
        score
      };
    }
  });

  resultBox.classList.remove("hidden");
  resultBox.innerHTML = `
    <h2>Your Best Career Match:</h2>
    <p class="score">${bestMatch.role} - ${bestMatch.score}% Match</p>

    <h3>Matched Skills</h3>
    <p>${bestMatch.matchedSkills.join(", ")}</p>

    <h3>Suggested Next Skills</h3>
    <ul>
      ${bestMatch.nextSkills.map(skill => `<li>${skill}</li>`).join("")}
    </ul>
  `;
}
