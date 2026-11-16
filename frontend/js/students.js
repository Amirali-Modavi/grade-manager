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
const refreshButton = document.querySelector("#refresh-button");
const searchInput = document.querySelector("#search-input");
const sortSelect = document.querySelector("#sort-select");
const performanceChart = document.querySelector("#performance-chart");
const editDialog = document.querySelector("#edit-dialog");
const editForm = document.querySelector("#edit-form");
const editName = document.querySelector("#edit-name");
const editGrades = document.querySelector("#edit-grades");
const editMessage = document.querySelector("#edit-message");
const toast = document.querySelector("#toast");
let allStudents = [];
let editingStudentId = null;

function showToast(message) {
    toast.textContent = message;
    toast.classList.add("show");
    window.setTimeout(() => toast.classList.remove("show"), 2600);
}

function parseGrades(rawValue) {
    const parts = rawValue.trim().split(/[\s,]+/).filter(Boolean);
    if (!parts.length) throw new Error("Enter at least one grade.");
    const grades = parts.map(Number);
    if (grades.some((grade) => !Number.isFinite(grade))) throw new Error("Grades must contain numbers only.");
    if (grades.some((grade) => grade < 0 || grade > 20)) throw new Error("Every grade must be between 0 and 20.");
    return grades;
}

function makeCell(text, className = "") {
    const cell = document.createElement("td");
    cell.textContent = text;
    if (className) cell.className = className;
    return cell;
}

async function loadSummary() {
    const response = await fetch("/api/reports/summary");
    if (!response.ok) throw new Error("Could not load class summary.");
    const summary = await response.json();
    totalStudents.textContent = summary.total_students;
    classAverage.textContent = Number(summary.class_average).toFixed(2);
    excellentCount.textContent = summary.excellent_count;
}

function renderChart(students) {
    performanceChart.replaceChildren();
    if (!students.length) {
        const note = document.createElement("p");
        note.className = "muted";
        note.textContent = "Add students to see the class performance chart.";
        performanceChart.append(note);
        return;
    }
    const ranked = [...students].sort((a, b) => b.average - a.average).slice(0, 8);
    for (const student of ranked) {
        const item = document.createElement("div");
        item.className = "chart-row";
        const label = document.createElement("span");
        label.className = "chart-name";
        label.textContent = student.name;
        const track = document.createElement("div");
        track.className = "chart-track";
        const fill = document.createElement("div");
        fill.className = "chart-fill";
        fill.style.width = `${Math.max(0, Math.min(100, student.average / 20 * 100))}%`;
        track.append(fill);
        const value = document.createElement("strong");
        value.textContent = student.average.toFixed(2);
        item.append(label, track, value);
        performanceChart.append(item);
    }
}

function renderStudents() {
    const searchTerm = searchInput.value.trim().toLocaleLowerCase();
    let visible = allStudents.filter((student) => student.name.toLocaleLowerCase().includes(searchTerm));
    const sortMode = sortSelect.value;
    if (sortMode === "average-desc") visible.sort((a, b) => b.average - a.average);
    else if (sortMode === "average-asc") visible.sort((a, b) => a.average - b.average);
    else visible.sort((a, b) => a.name.localeCompare(b.name));

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
    const rankLookup = [...allStudents].sort((a, b) => b.average - a.average);
    visible.forEach((student) => {
        const row = document.createElement("tr");
        const rank = rankLookup.findIndex((item) => item.id === student.id) + 1;
        const nameCell = makeCell("");
        const initial = document.createElement("span");
        initial.className = "student-initial";
        initial.textContent = student.name.trim().charAt(0).toUpperCase();
        nameCell.append(initial, document.createTextNode(student.name));
        row.append(
            makeCell(`#${rank}`), nameCell,
            makeCell(student.grades.map((grade) => Number(grade).toString()).join(", ")),
            makeCell(student.average.toFixed(2)),
            makeCell(student.letter_grade, "grade-cell"),
            makeCell(student.status, `status-cell status-${student.status.toLowerCase()}`),
        );
        const actionCell = document.createElement("td");
        const editButton = document.createElement("button");
        editButton.type = "button";
        editButton.className = "edit-button";
        editButton.textContent = "Edit";
        editButton.addEventListener("click", () => openEditDialog(student));
        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "delete-button";
        deleteButton.textContent = "Delete";
        deleteButton.addEventListener("click", () => deleteStudent(student.id, student.name));
        actionCell.append(editButton, deleteButton);
        row.append(actionCell);
        studentsBody.append(row);
    });
}

async function loadStudents() {
    loading.hidden = false;
    emptyState.hidden = true;
    studentsTable.hidden = true;
    try {
        const [studentsResponse] = await Promise.all([fetch("/api/reports/students"), loadSummary()]);
        if (!studentsResponse.ok) throw new Error("Could not load students.");
        allStudents = await studentsResponse.json();
        renderStudents();
        renderChart(allStudents);
        document.querySelector("#api-status").classList.add("online");
        document.querySelector("#api-status").innerHTML = "<i></i> Connected";
    } catch (error) {
        emptyState.hidden = false;
        emptyState.textContent = error.message;
        showToast(error.message);
        document.querySelector("#api-status").classList.add("offline");
        document.querySelector("#api-status").innerHTML = "<i></i> Disconnected";
    } finally {
        loading.hidden = true;
    }
}

function openEditDialog(student) {
    editingStudentId = student.id;
    editName.value = student.name;
    editGrades.value = student.grades.join(", ");
    editMessage.textContent = "";
    editMessage.className = "form-message";
    editDialog.showModal();
}

async function deleteStudent(studentId, studentName) {
    if (!window.confirm(`Are you sure you want to delete ${studentName}?`)) return;
    try {
        const response = await fetch(`/api/students/${encodeURIComponent(studentId)}`, { method: "DELETE" });
        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.detail || "Could not delete this student.");
        }
        showToast(`${studentName} was deleted.`);
        await loadStudents();
    } catch (error) { showToast(error.message); }
}

studentForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    formMessage.textContent = "";
    formMessage.className = "form-message";
    const name = nameInput.value.trim();
    if (!name) { formMessage.textContent = "Student name cannot be empty."; formMessage.classList.add("error"); return; }
    let grades;
    try { grades = parseGrades(gradesInput.value); }
    catch (error) { formMessage.textContent = error.message; formMessage.classList.add("error"); return; }
    submitButton.disabled = true;
    buttonLabel.textContent = "Saving...";
    try {
        const response = await fetch("/api/students", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, grades }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : "Please check the entered information.");
        studentForm.reset();
        formMessage.textContent = `${result.name} was added successfully.`;
        formMessage.classList.add("success");
        showToast("Student record saved.");
        await loadStudents();
    } catch (error) { formMessage.textContent = error.message; formMessage.classList.add("error"); }
    finally { submitButton.disabled = false; buttonLabel.textContent = "Add student"; }
});

editForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    let grades;
    try { grades = parseGrades(editGrades.value); }
    catch (error) { editMessage.textContent = error.message; editMessage.className = "form-message error"; return; }
    const saveButton = document.querySelector("#save-edit");
    saveButton.disabled = true;
    try {
        const response = await fetch(`/api/students/${encodeURIComponent(editingStudentId)}`, {
            method: "PUT", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: editName.value.trim(), grades }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : "Could not update this student.");
        editDialog.close();
        showToast(`${result.name} was updated.`);
        await loadStudents();
    } catch (error) { editMessage.textContent = error.message; editMessage.className = "form-message error"; }
    finally { saveButton.disabled = false; }
});

document.querySelector("#close-dialog").addEventListener("click", () => editDialog.close());
document.querySelector("#cancel-edit").addEventListener("click", () => editDialog.close());
searchInput.addEventListener("input", renderStudents);
sortSelect.addEventListener("change", renderStudents);
refreshButton.addEventListener("click", loadStudents);
loadStudents();
