const studentForm = document.querySelector("#student-form");
const nameInput = document.querySelector("#student-name");
const gradesInput = document.querySelector("#student-grades");
const submitButton = document.querySelector("#submit-button");
const buttonLabel = document.querySelector("#button-label");
const formMessage = document.querySelector("#form-message");
const studentsBody = document.querySelector("#students-body");
const studentsTable = document.querySelector("#students-table");
const loading = document.querySelector("#loading");
const emptyState = document.querySelector("#empty-state");
const totalStudents = document.querySelector("#total-students");
const classAverage = document.querySelector("#class-average");
const excellentCount = document.querySelector("#excellent-count");
const searchInput = document.querySelector("#search-input");
const sortSelect = document.querySelector("#sort-select");
const reportChart = document.querySelector("#report-chart");
const reportsBody = document.querySelector("#reports-body");
const reportsTable = document.querySelector("#reports-table");
const reportsEmpty = document.querySelector("#reports-empty");
const editDialog = document.querySelector("#edit-dialog");
const editForm = document.querySelector("#edit-form");
const editName = document.querySelector("#edit-name");
const editGrades = document.querySelector("#edit-grades");
const editMessage = document.querySelector("#edit-message");
const toast = document.querySelector("#toast");
const riskCard = document.querySelector("#risk-card");
const riskNames = document.querySelector("#report-at-risk-names");

let allStudents = [];
let editingStudentId = null;
let toastTimer = null;
let toastVersion = 0;
let loadVersion = 0;

function showToast(message, type = "success") {
    const thisToast = ++toastVersion;
    window.clearTimeout(toastTimer);
    toast.textContent = message;
    toast.dataset.type = type;
    toast.classList.add("show");
    toast.setAttribute("aria-hidden", "false");
    toastTimer = window.setTimeout(() => {
        if (thisToast !== toastVersion) return;
        toast.classList.remove("show");
        toast.setAttribute("aria-hidden", "true");
    }, 3000);
}

function setMessage(element, message, type = "error") {
    element.textContent = message;
    element.className = `form-message ${type}`;
    element.hidden = false;
}

function clearMessage(element) {
    element.textContent = "";
    element.className = "form-message";
    element.hidden = true;
}

function normalizeGradeInput(rawValue) {
    const persianDigits = "۰۱۲۳۴۵۶۷۸۹";
    const arabicDigits = "٠١٢٣٤٥٦٧٨٩";
    return Array.from(String(rawValue), (character) => {
        const persianIndex = persianDigits.indexOf(character);
        if (persianIndex !== -1) return String(persianIndex);
        const arabicIndex = arabicDigits.indexOf(character);
        if (arabicIndex !== -1) return String(arabicIndex);
        if (character === "٫") return ".";
        if (character === "،") return ",";
        if (character === "−") return "-";
        return character;
    }).join("");
}

function parseGrades(rawValue) {
    const normalized = normalizeGradeInput(rawValue).trim();
    if (!normalized) throw new Error("Enter at least one grade.");

    // A comma followed by a space is a list separator. A comma inside a
    // token is a decimal separator, so both `18, 19.5` and `18,5` work.
    let parts;
    if (/[\s;؛]/.test(normalized)) {
        parts = normalized.split(/(?:[\s;؛]+|[,،]\s+)/).filter(Boolean);
    } else {
        const commaCount = (normalized.match(/[,،]/g) || []).length;
        if (commaCount === 1 && !normalized.includes(".")) {
            // A single comma without surrounding whitespace is a decimal mark.
            parts = [normalized];
        } else if (commaCount > 0) {
            // Multiple commas, or comma-separated values with dot decimals,
            // are treated as a list. Use spaces/semicolons for decimal-comma lists.
            parts = normalized.split(/[,،]/).filter(Boolean);
        } else {
            parts = [normalized];
        }
    }

    const grades = parts.map((part) => {
        if (!/^[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)$/.test(part)) return Number.NaN;
        return Number(part.replace(",", "."));
    });
    if (!grades.length || grades.some((grade) => !Number.isFinite(grade))) {
        throw new Error("Enter valid numbers. Use spaces, semicolons, or commas followed by spaces between grades; use a comma or period for decimals.");
    }
    if (grades.some((grade) => grade < 0 || grade > 20)) {
        throw new Error("Every grade must be between 0 and 20.");
    }
    return grades;
}

function formatGrade(grade) {
    return Number(grade).toString();
}

function makeCell(label, className = "") {
    const cell = document.createElement("td");
    cell.dataset.label = label;
    if (className) cell.className = className;
    return cell;
}

function averageKey(average) {
    // API report averages are rounded to two decimal places; compare at that precision.
    return Math.round((Number(average) + Number.EPSILON) * 100);
}

function calculateRanks(students) {
    const ranked = [...students].sort((a, b) => {
        const difference = averageKey(b.average) - averageKey(a.average);
        return difference || a.name.localeCompare(b.name);
    });
    const ranks = new Map();
    let previousAverage = null;
    let currentRank = 0;

    ranked.forEach((student, index) => {
        const currentAverage = averageKey(student.average);
        if (previousAverage === null || currentAverage !== previousAverage) {
            currentRank = index + 1;
        }
        ranks.set(student.id, currentRank);
        previousAverage = currentAverage;
    });

    return { ranked, ranks };
}

function createNameCell(student) {
    const cell = makeCell("Student", "student-cell");
    const name = document.createElement("span");
    name.className = "student-name";
    name.textContent = student.name;
    name.title = student.name;
    cell.append(name);
    return cell;
}

function createGradesCell(grades) {
    const cell = makeCell("Grades", "grades-cell");
    const gradeList = document.createElement("div");
    gradeList.className = "grade-list";
    const completeList = grades.map(formatGrade).join(", ");
    gradeList.title = `All grades: ${completeList}`;
    gradeList.setAttribute("aria-label", `All grades: ${completeList}`);

    grades.slice(0, 4).forEach((grade) => {
        const chip = document.createElement("span");
        chip.className = "grade-chip";
        chip.textContent = formatGrade(grade);
        gradeList.append(chip);
    });

    if (grades.length > 4) {
        const more = document.createElement("span");
        more.className = "grade-chip grade-more";
        more.textContent = `+${grades.length - 4}`;
        more.title = completeList;
        gradeList.append(more);
    }

    cell.append(gradeList);
    return cell;
}

function createPerformanceBadge(student) {
    const badge = document.createElement("span");
    badge.className = `performance-badge status-${student.status.toLowerCase()}`;
    badge.textContent = `${student.letter_grade} · ${student.status}`;
    return badge;
}

function createActionsCell(student) {
    const cell = makeCell("Actions", "actions-cell");
    const actions = document.createElement("div");
    actions.className = "row-actions";

    const editButton = document.createElement("button");
    editButton.type = "button";
    editButton.className = "edit-button";
    editButton.textContent = "Edit";
    editButton.title = `Edit ${student.name}`;
    editButton.setAttribute("aria-label", `Edit ${student.name}`);
    editButton.addEventListener("click", () => openEditDialog(student));

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "delete-button";
    deleteButton.textContent = "Delete";
    deleteButton.title = `Delete ${student.name}`;
    deleteButton.setAttribute("aria-label", `Delete ${student.name}`);
    deleteButton.addEventListener("click", () => deleteStudent(student.id, student.name));

    actions.append(editButton, deleteButton);
    cell.append(actions);
    return cell;
}

function createStudentRow(student, rank, includeActions = false) {
    const row = document.createElement("tr");
    const rankCell = makeCell("Rank", "rank-cell");
    rankCell.textContent = `#${rank}`;
    const averageCell = makeCell("Average", "average-cell");
    averageCell.textContent = Number(student.average).toFixed(2);
    const badgeCell = makeCell("Grade / status", "badge-cell");
    badgeCell.append(createPerformanceBadge(student));

    row.append(rankCell, createNameCell(student), createGradesCell(student.grades), averageCell, badgeCell);
    if (includeActions) row.append(createActionsCell(student));
    return row;
}

function renderStudents() {
    const searchTerm = searchInput.value.trim().toLocaleLowerCase();
    const { ranks } = calculateRanks(allStudents);
    let visible = allStudents.filter((student) => student.name.toLocaleLowerCase().includes(searchTerm));
    const sortMode = sortSelect.value;

    if (sortMode === "name-asc") {
        visible.sort((a, b) => a.name.localeCompare(b.name));
    } else if (sortMode === "name-desc") {
        visible.sort((a, b) => b.name.localeCompare(a.name));
    } else if (sortMode === "average-asc") {
        visible.sort((a, b) => averageKey(a.average) - averageKey(b.average) || a.name.localeCompare(b.name));
    } else {
        // Rank and highest-average use the same full-class ordering, independent of search.
        visible.sort((a, b) => {
            const difference = averageKey(b.average) - averageKey(a.average);
            return difference || a.name.localeCompare(b.name);
        });
    }

    studentsBody.replaceChildren();
    if (!allStudents.length) {
        studentsTable.hidden = true;
        emptyState.hidden = false;
        emptyState.textContent = "No students yet. Add your first student using the form.";
        return;
    }
    if (!visible.length) {
        studentsTable.hidden = true;
        emptyState.hidden = false;
        emptyState.textContent = "No students match your search.";
        return;
    }

    emptyState.hidden = true;
    studentsTable.hidden = false;
    visible.forEach((student) => {
        studentsBody.append(createStudentRow(student, ranks.get(student.id), true));
    });

}

function renderPerformanceChart(students, passingThreshold) {
    reportChart.replaceChildren();
    if (!students.length) {
        const note = document.createElement("p");
        note.className = "muted";
        note.textContent = "Add students to see the class performance chart.";
        reportChart.append(note);
        return;
    }

    const { ranked } = calculateRanks(students);
    const chart = document.createElement("div");
    chart.className = "chart-content";

    const note = document.createElement("p");
    note.className = "chart-note";
    note.textContent = students.length > 12
        ? `Showing the top 12 of ${students.length} students by average. Passing threshold: ${passingThreshold}/20.`
        : `Showing all ${students.length} students. Passing threshold: ${passingThreshold}/20.`;
    chart.append(note);

    const axisRow = document.createElement("div");
    axisRow.className = "chart-axis-row";
    const axisSpacer = document.createElement("span");
    axisSpacer.setAttribute("aria-hidden", "true");
    const axis = document.createElement("div");
    axis.className = "chart-axis";
    ["0", "5", "10", "15", "20"].forEach((value) => {
        const tick = document.createElement("span");
        tick.textContent = value;
        axis.append(tick);
    });
    const axisValueSpacer = document.createElement("span");
    axisValueSpacer.setAttribute("aria-hidden", "true");
    axisRow.append(axisSpacer, axis, axisValueSpacer);
    chart.append(axisRow);

    ranked.slice(0, 12).forEach((student) => {
        const row = document.createElement("div");
        row.className = "chart-row";
        const label = document.createElement("span");
        label.className = "chart-name";
        label.textContent = student.name;
        label.title = student.name;

        const track = document.createElement("div");
        track.className = "chart-track";
        track.setAttribute("role", "img");
        track.setAttribute("aria-label", `${student.name}: ${Number(student.average).toFixed(2)} out of 20, ${student.status}; passing threshold ${passingThreshold}`);
        track.style.setProperty("--passing-position", `${Number(passingThreshold) / 20 * 100}%`);
        const fill = document.createElement("div");
        fill.className = `chart-fill status-${student.status.toLowerCase()}`;
        fill.style.width = `${Math.max(0, Math.min(100, Number(student.average) / 20 * 100))}%`;
        track.append(fill);

        const value = document.createElement("strong");
        value.textContent = Number(student.average).toFixed(2);
        row.append(label, track, value);
        chart.append(row);
    });

    reportChart.append(chart);
}

function renderRiskCard(students) {
    const atRisk = students.filter((student) => student.status === "Failing");
    document.querySelector("#report-at-risk").textContent = String(atRisk.length);
    riskCard.classList.toggle("has-risk", atRisk.length > 0);
    riskCard.classList.toggle("risk-clear", atRisk.length === 0);
    riskNames.replaceChildren();

    if (!atRisk.length) {
        riskNames.textContent = "No students currently at risk.";
        return;
    }

    atRisk.forEach((student, index) => {
        if (index) riskNames.append(document.createTextNode(", "));
        const name = document.createElement("span");
        name.className = "risk-name";
        name.textContent = student.name;
        name.title = student.name;
        riskNames.append(name);
    });
}

function renderReports(students, passingThreshold) {
    reportsBody.replaceChildren();
    const { ranked, ranks } = calculateRanks(students);

    if (!students.length) {
        reportsEmpty.hidden = false;
        reportsTable.hidden = true;
        document.querySelector("#report-class-average").textContent = "—";
        document.querySelector("#report-highest").textContent = "—";
        document.querySelector("#report-highest-name").textContent = "No student data";
        renderRiskCard([]);
        renderPerformanceChart([], passingThreshold);
        return;
    }

    reportsEmpty.hidden = true;
    reportsTable.hidden = false;
    const classAverageValue = students.reduce((sum, student) => sum + Number(student.average), 0) / students.length;
    const highest = ranked[0];

    document.querySelector("#report-class-average").textContent = classAverageValue.toFixed(2);
    document.querySelector("#report-highest").textContent = Number(highest.average).toFixed(2);
    document.querySelector("#report-highest-name").textContent = highest.name;
    renderRiskCard(students);

    ranked.forEach((student) => {
        reportsBody.append(createStudentRow(student, ranks.get(student.id)));
    });
    renderPerformanceChart(students, passingThreshold);
}

async function loadStudents() {
    const requestVersion = ++loadVersion;
    if (!allStudents.length) loading.hidden = false;
    emptyState.hidden = true;

    try {
        const response = await fetch("/api/reports/overview");
        if (!response.ok) throw new Error("Could not load student reports.");
        const overview = await response.json();
        const { students, summary } = overview;
        if (requestVersion !== loadVersion) return;

        totalStudents.textContent = summary.total_students;
        classAverage.textContent = Number(summary.class_average).toFixed(2);
        excellentCount.textContent = summary.excellent_count;
        allStudents = students;
        renderStudents();
        renderReports(allStudents, Number(summary.passing_threshold));
        setApiStatus("online", "Backend connected");
    } catch (error) {
        if (requestVersion !== loadVersion) return;
        if (!allStudents.length) {
            studentsTable.hidden = true;
            emptyState.hidden = false;
            emptyState.textContent = error.message;
        }
        showToast(error.message, "error");
        setApiStatus("offline", "Backend disconnected");
    } finally {
        if (requestVersion === loadVersion) loading.hidden = true;
    }
}

function openEditDialog(student) {
    editingStudentId = student.id;
    editName.value = student.name;
    editGrades.value = student.grades.join(", ");
    clearMessage(editMessage);
    editDialog.showModal();
    editName.focus();
}

async function deleteStudent(studentId, studentName) {
    if (!window.confirm(`Are you sure you want to delete ${studentName}?`)) return;
    try {
        const response = await fetch(`/api/students/${encodeURIComponent(studentId)}`, { method: "DELETE" });
        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.detail || "Could not delete this student.");
        }
        await loadStudents();
        showToast(`${studentName} was deleted.`);
    } catch (error) {
        showToast(error.message, "error");
    }
}

studentForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage(formMessage);
    const name = nameInput.value.trim();
    if (!name) {
        setMessage(formMessage, "Student name cannot be empty.");
        return;
    }

    let grades;
    try {
        grades = parseGrades(gradesInput.value);
    } catch (error) {
        setMessage(formMessage, error.message);
        return;
    }

    submitButton.disabled = true;
    buttonLabel.textContent = "Saving...";
    try {
        const response = await fetch("/api/students", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, grades }),
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(typeof result.detail === "string" ? result.detail : "Please check the entered information.");
        }
        studentForm.reset();
        await loadStudents();
        showToast(`${result.name} was added successfully.`);
    } catch (error) {
        setMessage(formMessage, error.message);
    } finally {
        submitButton.disabled = false;
        buttonLabel.textContent = "Add student";
    }
});

editForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage(editMessage);

    const name = editName.value.trim();
    if (!name) {
        setMessage(editMessage, "Student name cannot be empty.");
        return;
    }

    let grades;
    try {
        grades = parseGrades(editGrades.value);
    } catch (error) {
        setMessage(editMessage, error.message);
        return;
    }

    const saveButton = document.querySelector("#save-edit");
    saveButton.disabled = true;
    try {
        const response = await fetch(`/api/students/${encodeURIComponent(editingStudentId)}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, grades }),
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(typeof result.detail === "string" ? result.detail : "Could not update this student.");
        }
        editDialog.close();
        await loadStudents();
        showToast(`${result.name} was updated.`);
    } catch (error) {
        setMessage(editMessage, error.message);
    } finally {
        saveButton.disabled = false;
    }
});

document.querySelector("#close-dialog").addEventListener("click", () => editDialog.close());
document.querySelector("#cancel-edit").addEventListener("click", () => editDialog.close());
searchInput.addEventListener("input", renderStudents);
sortSelect.addEventListener("change", renderStudents);
window.addEventListener("grade-manager:view-change", () => loadStudents());
loadStudents();
