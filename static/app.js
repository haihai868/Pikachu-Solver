// Pikachu Board Solver - Frontend Application Logic

// API Config
const API_URL = window.location.origin;

// State Variables
let currentGrid = [];     // 9x16 grid containing values 0..36
let initialGrid = [];     // Backup of the loaded grid
let steps = [];           // Solved steps list
let currentStepIndex = -1;// Currently active step index (-1 = initial state)
let isPlaying = false;    // Auto play status
let playInterval = null;  // Interval timer
let speed = 1.0;          // Playback speed in seconds
let isEditing = false;    // Grid editing state
let selectedCell = null;  // Currently editing cell {row, col}
let originalBoardBase64 = ""; // Backup of B64 board image
let tileImages = [];      // Array of 144 cropped tile Base64 strings
let boardStates = [];     // Array of precomputed grids (length steps.length + 1)

// DOM Elements
const uploadBox = document.getElementById("upload-box");
const fileInput = document.getElementById("file-input");
const visualizerWrapper = document.getElementById("visualizer-wrapper");
const boardContainer = document.getElementById("board-container");
const boardImage = document.getElementById("board-image");
const pathCanvas = document.getElementById("path-canvas");
const gridOverlay = document.getElementById("grid-overlay");
const boardStatus = document.getElementById("board-status");
const btnEdit = document.getElementById("btn-edit");
const btnSolveEdited = document.getElementById("btn-solve-edited");
const warningBox = document.getElementById("warning-box");
const warningText = document.getElementById("warning-text");
const playbackSection = document.getElementById("playback-section");
const btnPlay = document.getElementById("btn-play");
const btnPrev = document.getElementById("btn-prev");
const btnNext = document.getElementById("btn-next");
const btnReset = document.getElementById("btn-reset");
const speedSlider = document.getElementById("speed-slider");
const speedValue = document.getElementById("speed-value");
const solvedCount = document.getElementById("solved-count");
const totalCount = document.getElementById("total-count");
const progressFill = document.getElementById("progress-fill");
const stepsList = document.getElementById("steps-list");
const levelSelect = document.getElementById("level-select");

// Modal Elements
const editModal = document.getElementById("edit-modal");
const tilePickerGrid = document.getElementById("tile-picker-grid");
const btnClearTile = document.getElementById("btn-clear-tile");
const closeModal = document.getElementById("close-modal");

// Initialize application
function init() {
    setupEventListeners();
    setupTilePicker();
}

// Set up DOM event listeners
function setupEventListeners() {
    // File upload
    uploadBox.addEventListener("click", () => fileInput.click());
    uploadBox.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadBox.classList.add("hover");
    });
    uploadBox.addEventListener("dragleave", () => uploadBox.classList.remove("hover"));
    uploadBox.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadBox.classList.remove("hover");
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Playback Controls
    btnPlay.addEventListener("click", togglePlay);
    btnPrev.addEventListener("click", () => { stopAutoPlay(); stepPrevious(); });
    btnNext.addEventListener("click", () => { stopAutoPlay(); stepNext(); });
    btnReset.addEventListener("click", () => { stopAutoPlay(); resetPlayback(); });
    
    speedSlider.addEventListener("input", (e) => {
        speed = parseFloat(e.target.value);
        speedValue.textContent = speed.toFixed(1);
        if (isPlaying) {
            startAutoPlay(); // Restart with new speed
        }
    });

    // Edit Grid Mode
    btnEdit.addEventListener("click", toggleEditMode);
    btnSolveEdited.addEventListener("click", solveEditedGrid);

    // Level Selection Change
    levelSelect.addEventListener("change", () => {
        stopAutoPlay();
        if (originalBoardBase64) {
            solveGridWithLevel();
        }
    });

    // Modal Close
    closeModal.addEventListener("click", () => editModal.style.display = "none");
    btnClearTile.addEventListener("click", () => {
        if (selectedCell) {
            updateCell(selectedCell.row, selectedCell.col, 0);
            editModal.style.display = "none";
        }
    });

    // Handle canvas resizing when board image is loaded
    boardImage.addEventListener("load", onBoardImageLoad);
    window.addEventListener("resize", resizeCanvas);
}

// Generate the 36 class picker options inside the modal
function setupTilePicker() {
    tilePickerGrid.innerHTML = "";
    for (let i = 1; i <= 36; i++) {
        const item = document.createElement("div");
        item.className = "picker-item";
        item.style.setProperty("--tile-hue", i * 10);
        item.innerHTML = `${i}<span>Loại ${i}</span>`;
        item.addEventListener("click", () => {
            if (selectedCell) {
                updateCell(selectedCell.row, selectedCell.col, i);
                editModal.style.display = "none";
            }
        });
        tilePickerGrid.appendChild(item);
    }
}

// Resize path canvas to overlay exactly on the board image + margin
function resizeCanvas() {
    if (!boardImage.src) return;
    const w = boardImage.clientWidth;
    const h = boardImage.clientHeight;
    
    // Canvas has -30px offset on top/left, so width/height must include +60px
    pathCanvas.width = w + 60;
    pathCanvas.height = h + 60;
    
    // Redraw path if any
    drawActivePath();
}

// Send uploaded file to FastAPI server
async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append("file", file);

    // Visual indicators
    uploadBox.querySelector("h3").textContent = "Đang xử lý hình ảnh...";
    uploadBox.querySelector("p").textContent = "Vui lòng chờ nhận diện bảng...";
    uploadBox.querySelector(".upload-icon").className = "fa-solid fa-spinner fa-spin upload-icon";

    try {
        const selectedLevel = parseInt(levelSelect.value);
        const res = await fetch(`${API_URL}/api/solve?level=${selectedLevel}`, {
            method: "POST",
            body: formData
        });

        const text = await res.text();
        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            throw new Error(`Lỗi kết nối hoặc phản hồi không hợp lệ từ máy chủ (HTTP ${res.status})`);
        }

        if (!res.ok) {
            throw new Error(data.detail || "Không thể xử lý hình ảnh");
        }
        originalBoardBase64 = data.board_img;
        
        // Save states
        currentGrid = JSON.parse(JSON.stringify(data.grid));
        initialGrid = JSON.parse(JSON.stringify(data.grid));
        steps = data.steps;

        // Render board UI
        renderGrid(currentGrid);
        
        // Show board image container (remove hidden so load event fires and calculates dimensions)
        boardImage.classList.remove("hidden");
        renderCroppedBoard(data.board_img);
        renderStepsList();

        // Warning messages
        if (data.error) {
            warningBox.style.display = "flex";
            warningText.textContent = data.error;
        } else {
            warningBox.style.display = "none";
        }

        // Adjust state
        boardStatus.textContent = data.success ? "Đã giải thành công" : "Bảng bị kẹt / Lỗi khớp cặp";
        boardStatus.className = data.success ? "badge active" : "badge";
        
        btnEdit.disabled = false;
        
        // Show playback controls if successful
        if (data.success && steps.length > 0) {
            playbackSection.style.display = "flex";
            totalCount.textContent = steps.length;
        } else {
            playbackSection.style.display = "none";
        }

        // Show visualizer
        uploadBox.style.display = "none";
        visualizerWrapper.style.display = "flex";
        
    } catch (e) {
        alert("Lỗi: " + e.message);
        // Reset upload box
        uploadBox.querySelector("h3").textContent = "Kéo thả ảnh vào đây";
        uploadBox.querySelector("p").textContent = "hoặc click để chọn tệp từ máy tính";
        uploadBox.querySelector(".upload-icon").className = "fa-solid fa-cloud-arrow-up upload-icon";
    }
}

// Display the cropped board image
function renderCroppedBoard(base64) {
    boardImage.src = `data:image/png;base64,${base64}`;
}

// Render the 9x16 grid overlay on top of the board screenshot
function renderGrid(grid) {
    gridOverlay.innerHTML = "";
    for (let r = 0; r < 9; r++) {
        for (let c = 0; c < 16; c++) {
            const val = grid[r][c];
            const cell = document.createElement("div");
            cell.className = "grid-cell";
            cell.dataset.row = r;
            cell.dataset.col = c;
            
            if (val === 0) {
                cell.classList.add("empty");
            } else {
                cell.style.setProperty("--tile-hue", val * 10);
                cell.textContent = val;
            }

            // Click listener for edit mode
            cell.addEventListener("click", () => {
                if (isEditing) {
                    selectedCell = { row: r, col: c };
                    editModal.style.display = "flex";
                }
            });

            gridOverlay.appendChild(cell);
        }
    }
}

// Toggle grid Edit Mode
function toggleEditMode() {
    isEditing = !isEditing;
    
    if (isEditing) {
        stopAutoPlay();
        btnEdit.innerHTML = '<i class="fa-solid fa-xmark"></i> Hủy Chỉnh Sửa';
        btnEdit.className = "btn btn-secondary";
        btnSolveEdited.style.display = "flex";
        playbackSection.style.display = "none";
        
        // Enable click events on grid cells
        gridOverlay.style.pointerEvents = "auto";
        document.querySelectorAll(".grid-cell").forEach(c => c.classList.add("edit-mode"));
    } else {
        // Reset grid to initial
        currentGrid = JSON.parse(JSON.stringify(initialGrid));
        renderGrid(currentGrid);
        
        btnEdit.innerHTML = '<i class="fa-solid fa-pen-to-square"></i> Chỉnh Sửa Bảng';
        btnEdit.className = "btn btn-secondary";
        btnSolveEdited.style.display = "none";
        
        if (steps.length > 0) {
            playbackSection.style.display = "flex";
            resetPlayback();
        }
        
        gridOverlay.style.pointerEvents = "none";
        document.querySelectorAll(".grid-cell").forEach(c => c.classList.remove("edit-mode"));
    }
}

// Update value of a specific cell in Edit Mode
function updateCell(r, c, value) {
    currentGrid[r][c] = value;
    const cellIdx = r * 16 + c;
    const cell = gridOverlay.children[cellIdx];
    
    if (value === 0) {
        cell.className = "grid-cell empty edit-mode";
        cell.textContent = "";
        cell.style.removeProperty("--tile-hue");
    } else {
        cell.className = "grid-cell edit-mode";
        cell.style.setProperty("--tile-hue", value * 10);
        cell.textContent = value;
    }
}

// Send the manually corrected grid to the backend for re-solving
async function solveEditedGrid() {
    try {
        const selectedLevel = parseInt(levelSelect.value);
        const res = await fetch(`${API_URL}/api/solve_grid`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ grid: currentGrid, level: selectedLevel })
        });

        const text = await res.text();
        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            throw new Error(`Lỗi kết nối hoặc phản hồi không hợp lệ từ máy chủ (HTTP ${res.status})`);
        }

        if (!res.ok) {
            throw new Error(data.detail || "Lỗi giải grid");
        }
        
        // Update states
        initialGrid = JSON.parse(JSON.stringify(currentGrid));
        steps = data.steps;

        // Render steps sidebar
        renderStepsList();

        // Warning messages
        if (data.error) {
            warningBox.style.display = "flex";
            warningText.textContent = data.error;
        } else {
            warningBox.style.display = "none";
        }

        // Adjust state
        boardStatus.textContent = data.success ? "Đã giải thành công" : "Bảng bị kẹt / Lỗi khớp cặp";
        boardStatus.className = data.success ? "badge active" : "badge";
        
        // Exit Edit Mode
        isEditing = false;
        btnEdit.innerHTML = '<i class="fa-solid fa-pen-to-square"></i> Chỉnh Sửa Bảng';
        btnEdit.className = "btn btn-secondary";
        btnSolveEdited.style.display = "none";
        gridOverlay.style.pointerEvents = "none";
        document.querySelectorAll(".grid-cell").forEach(c => c.classList.remove("edit-mode"));

        // Setup playback
        extractTiles(2);
        precomputeBoardStates();
        
        if (data.success && steps.length > 0) {
            playbackSection.style.display = "flex";
            totalCount.textContent = steps.length;
            resetPlayback();
        } else {
            playbackSection.style.display = "none";
            resetPlayback();
        }

    } catch (e) {
        alert("Lỗi giải bảng đã sửa: " + e.message);
    }
}

// Populate the side panel with solved steps
function renderStepsList() {
    stepsList.innerHTML = "";
    if (steps.length === 0) {
        stepsList.innerHTML = '<div class="no-steps">Không tìm thấy bước giải nào.</div>';
        return;
    }

    steps.forEach((step, idx) => {
        const item = document.createElement("div");
        item.className = "step-item";
        item.id = `step-item-${idx}`;
        
        // Start/end 1-indexed for display
        const r1 = step.start[0] + 1;
        const c1 = step.start[1] + 1;
        const r2 = step.end[0] + 1;
        const c2 = step.end[1] + 1;

        item.innerHTML = `
            <span class="step-num">#${idx + 1}</span>
            <div class="step-badge" style="--tile-hue: ${step.value * 10}">${step.value}</div>
            <div class="step-desc">Khớp cặp ô <strong>(${r1}, ${c1})</strong> và <strong>(${r2}, ${c2})</strong></div>
        `;

        item.addEventListener("click", () => {
            stopAutoPlay();
            showStep(idx);
        });

        stepsList.appendChild(item);
    });
}

// Playback playback states
function resetPlayback() {
    currentStepIndex = -1;
    showGridAtStep(-1);
    clearCanvas();
    updatePlaybackUI();
}

function togglePlay() {
    if (isPlaying) {
        stopAutoPlay();
    } else {
        startAutoPlay();
    }
}

function startAutoPlay() {
    isPlaying = true;
    btnPlay.innerHTML = '<i class="fa-solid fa-pause"></i>';
    btnPlay.title = "Tạm dừng";
    
    // Clear existing interval
    if (playInterval) clearInterval(playInterval);
    
    // If we are at the end, wrap to start
    if (currentStepIndex >= steps.length - 1) {
        currentStepIndex = -1;
    }
    
    stepNext(); // Do one step immediately
    
    playInterval = setInterval(() => {
        if (currentStepIndex < steps.length - 1) {
            stepNext();
        } else {
            stopAutoPlay();
        }
    }, speed * 1000 + 400); // add margin for animation duration
}

function stopAutoPlay() {
    isPlaying = false;
    btnPlay.innerHTML = '<i class="fa-solid fa-play"></i>';
    btnPlay.title = "Chạy tự động";
    if (playInterval) {
        clearInterval(playInterval);
        playInterval = null;
    }
}

function stepNext() {
    if (currentStepIndex < steps.length - 1) {
        showStep(currentStepIndex + 1);
    }
}

function stepPrevious() {
    if (currentStepIndex > -1) {
        showStep(currentStepIndex - 1);
    }
}

// Animate and transition to step `idx`
function showStep(idx) {
    if (idx === currentStepIndex) return;
    
    // If stepping forward (normal flow), animate the transition
    if (idx === currentStepIndex + 1) {
        currentStepIndex = idx;
        animateStep(steps[currentStepIndex]);
    } else {
        // Jump directly to that state
        currentStepIndex = idx;
        showGridAtStep(currentStepIndex);
        clearCanvas();
        drawActivePath();
        updatePlaybackUI();
    }
}

// Render the grid values at a specific step in history
function showGridAtStep(stepIdx) {
    if (boardStates.length > 0) {
        // boardStates[0] is initial state (stepIdx = -1)
        // boardStates[stepIdx + 1] is state after stepIdx
        const state = boardStates[stepIdx + 1];
        
        for (let r = 0; r < 9; r++) {
            for (let c = 0; c < 16; c++) {
                const cellState = state[r][c];
                const val = cellState.value;
                const cellIdx = r * 16 + c;
                const cell = gridOverlay.children[cellIdx];
                
                if (val === 0) {
                    cell.classList.add("empty");
                    cell.textContent = "";
                    cell.style.backgroundImage = "none";
                    cell.style.removeProperty("--tile-hue");
                } else {
                    cell.classList.remove("empty");
                    cell.style.setProperty("--tile-hue", val * 10);
                    if (cellState.imageSrc) {
                        cell.style.backgroundImage = `url(${cellState.imageSrc})`;
                        cell.style.backgroundSize = "cover";
                    } else {
                        cell.style.backgroundImage = "none";
                    }
                    cell.textContent = val;
                }
                cell.classList.remove("matched-highlight", "fade-out");
            }
        }
    } else {
        // Fallback
        const tempGrid = JSON.parse(JSON.stringify(initialGrid));
        for (let i = 0; i <= stepIdx; i++) {
            const step = steps[i];
            tempGrid[step.start[0]][step.start[1]] = 0;
            tempGrid[step.end[0]][step.end[1]] = 0;
        }
        for (let r = 0; r < 9; r++) {
            for (let c = 0; c < 16; c++) {
                const val = tempGrid[r][c];
                const cellIdx = r * 16 + c;
                const cell = gridOverlay.children[cellIdx];
                if (val === 0) {
                    cell.classList.add("empty");
                    cell.textContent = "";
                    cell.style.backgroundImage = "none";
                } else {
                    cell.classList.remove("empty");
                    cell.style.setProperty("--tile-hue", val * 10);
                    cell.textContent = val;
                    cell.style.backgroundImage = "none";
                }
                cell.classList.remove("matched-highlight", "fade-out");
            }
        }
    }
}

// Draw the connecting line for the current step (non-animated representation)
function drawActivePath() {
    clearCanvas();
    if (currentStepIndex < 0 || currentStepIndex >= steps.length) return;
    
    const step = steps[currentStepIndex];
    drawLaserPath(step.path, step.value, 1.0); // opacity = 1.0
}

// Clear drawing canvas
function clearCanvas() {
    const ctx = pathCanvas.getContext("2d");
    ctx.clearRect(0, 0, pathCanvas.width, pathCanvas.height);
}

// Animate a single step with laser connection and fade outs
function animateStep(step) {
    // 1. Reset board to the state *before* this step is resolved
    showGridAtStep(currentStepIndex - 1);
    clearCanvas();
    
    // Highlight the starting and ending tiles
    const cellIdx1 = step.start[0] * 16 + step.start[1];
    const cellIdx2 = step.end[0] * 16 + step.end[1];
    const cell1 = gridOverlay.children[cellIdx1];
    const cell2 = gridOverlay.children[cellIdx2];
    cell1.classList.add("matched-highlight");
    cell2.classList.add("matched-highlight");
    
    // 2. Animate the path line drawing
    const path = step.path;
    const ctx = pathCanvas.getContext("2d");
    const cellW = boardImage.clientWidth / 16;
    const cellH = boardImage.clientHeight / 9;
    
    // Convert path indices to canvas coordinates (include +30px offset)
    const points = path.map(p => ({
        x: (p[1] + 0.5) * cellW + 30,
        y: (p[0] + 0.5) * cellH + 30
    }));
    
    let segmentIdx = 0;
    let progress = 0; // 0 to 1
    
    // Set style of laser line
    const color = `hsl(${step.value * 10}, 100%, 65%)`;
    
    function animateLaser() {
        if (segmentIdx >= points.length - 1) {
            // Animation finished!
            // 3. Trigger cell fade-out shrink animation
            cell1.classList.add("fade-out");
            cell2.classList.add("fade-out");
            
            // 4. Update the board state to clear these cells in 350ms
            setTimeout(() => {
                showGridAtStep(currentStepIndex);
                clearCanvas();
                updatePlaybackUI();
            }, 350);
            return;
        }
        
        // Draw up to the current progress of the current segment
        ctx.clearRect(0, 0, pathCanvas.width, pathCanvas.height);
        
        // Draw already completed segments
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 4;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.shadowColor = color;
        ctx.shadowBlur = 12;
        
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i <= segmentIdx; i++) {
            ctx.lineTo(points[i].x, points[i].y);
        }
        
        // Interpolate the current segment
        const pStart = points[segmentIdx];
        const pEnd = points[segmentIdx + 1];
        const curX = pStart.x + (pEnd.x - pStart.x) * progress;
        const curY = pStart.y + (pEnd.y - pStart.y) * progress;
        ctx.lineTo(curX, curY);
        ctx.stroke();
        
        // Increment progress
        progress += 0.25; // Speed multiplier of line drawing
        if (progress > 1) {
            progress = 0;
            segmentIdx++;
        }
        
        requestAnimationFrame(animateLaser);
    }
    
    animateLaser();
}

// Draw static laser path (fallback)
function drawLaserPath(path, value, opacity) {
    if (path.length < 2) return;
    const ctx = pathCanvas.getContext("2d");
    const cellW = boardImage.clientWidth / 16;
    const cellH = boardImage.clientHeight / 9;
    
    const color = `hsla(${value * 10}, 100%, 65%, ${opacity})`;
    
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 4;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.shadowColor = color;
    ctx.shadowBlur = 10;
    
    const startX = (path[0][1] + 0.5) * cellW + 30;
    const startY = (path[0][0] + 0.5) * cellH + 30;
    ctx.moveTo(startX, startY);
    
    for (let i = 1; i < path.length; i++) {
        const nextX = (path[i][1] + 0.5) * cellW + 30;
        const nextY = (path[i][0] + 0.5) * cellH + 30;
        ctx.lineTo(nextX, nextY);
    }
    ctx.stroke();
}

// Sync the playback control elements with states
function updatePlaybackUI() {
    solvedCount.textContent = currentStepIndex + 1;
    
    const pct = steps.length > 0 ? ((currentStepIndex + 1) / steps.length) * 100 : 0;
    progressFill.style.width = `${pct}%`;
    
    // Highlight step item in list
    document.querySelectorAll(".step-item").forEach(item => item.classList.remove("active"));
    if (currentStepIndex >= 0) {
        const activeItem = document.getElementById(`step-item-${currentStepIndex}`);
        if (activeItem) {
            activeItem.classList.add("active");
            activeItem.scrollIntoView({ block: "nearest", behavior: "smooth" });
        }
    }
}

// Image loaded handler
function onBoardImageLoad() {
    resizeCanvas();
    extractTiles(2);
    boardImage.classList.add("hidden");
    precomputeBoardStates();
    resetPlayback();
}

// Gap-aware slicing of tiles from board image
function extractTiles(gap = 2) {
    tileImages = [];
    const img = boardImage;
    if (!img.naturalWidth) return;
    
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    
    const naturalW = img.naturalWidth;
    const naturalH = img.naturalHeight;
    
    const tileW = (naturalW - (16 - 1) * gap) / 16;
    const tileH = (naturalH - (9 - 1) * gap) / 9;
    
    canvas.width = tileW;
    canvas.height = tileH;
    
    for (let r = 0; r < 9; r++) {
        for (let c = 0; c < 16; c++) {
            const sx = c * (tileW + gap);
            const sy = r * (tileH + gap);
            
            ctx.clearRect(0, 0, tileW, tileH);
            ctx.drawImage(img, sx, sy, tileW, tileH, 0, 0, tileW, tileH);
            
            const dataUrl = canvas.toDataURL("image/png");
            tileImages.push(dataUrl);
        }
    }
}

// Shift logic matching 9 Pikachu levels
function applyGravityJS(grid, level) {
    if (level === 1) return grid;
    const rows = 9;
    const cols = 16;
    
    // Column-based shifting (Level 2, 3, 6, 7)
    if (level === 2 || level === 3 || level === 6 || level === 7) {
        for (let c = 0; c < cols; c++) {
            const activeCol = [];
            for (let r = 0; r < rows; r++) {
                activeCol.push(grid[r][c]);
            }
            const nonZeros = activeCol.filter(cell => cell.value !== 0);
            
            if (level === 2) { // Down
                const emptyCount = rows - nonZeros.length;
                const newCol = [];
                for (let r = 0; r < emptyCount; r++) {
                    newCol.push({ value: 0, imageSrc: null });
                }
                newCol.push(...nonZeros);
                for (let r = 0; r < rows; r++) {
                    grid[r][c] = newCol[r];
                }
            } else if (level === 3) { // Up
                const emptyCount = rows - nonZeros.length;
                const newCol = [...nonZeros];
                for (let r = 0; r < emptyCount; r++) {
                    newCol.push({ value: 0, imageSrc: null });
                }
                for (let r = 0; r < rows; r++) {
                    grid[r][c] = newCol[r];
                }
            } else if (level === 6) { // Vertical Center
                const topHalf = activeCol.slice(0, 5);
                const botHalf = activeCol.slice(5, 9);
                
                const topNonZeros = topHalf.filter(cell => cell.value !== 0);
                const botNonZeros = botHalf.filter(cell => cell.value !== 0);
                
                const newTop = [];
                const topEmpty = 5 - topNonZeros.length;
                for (let r = 0; r < topEmpty; r++) {
                    newTop.push({ value: 0, imageSrc: null });
                }
                newTop.push(...topNonZeros);
                
                const newBot = [...botNonZeros];
                const botEmpty = 4 - botNonZeros.length;
                for (let r = 0; r < botEmpty; r++) {
                    newBot.push({ value: 0, imageSrc: null });
                }
                
                const newCol = [...newTop, ...newBot];
                for (let r = 0; r < rows; r++) {
                    grid[r][c] = newCol[r];
                }
            } else if (level === 7) { // Vertical Sides
                const topHalf = activeCol.slice(0, 5);
                const botHalf = activeCol.slice(5, 9);
                
                const topNonZeros = topHalf.filter(cell => cell.value !== 0);
                const botNonZeros = botHalf.filter(cell => cell.value !== 0);
                
                const newTop = [...topNonZeros];
                const topEmpty = 5 - topNonZeros.length;
                for (let r = 0; r < topEmpty; r++) {
                    newTop.push({ value: 0, imageSrc: null });
                }
                
                const newBot = [];
                const botEmpty = 4 - botNonZeros.length;
                for (let r = 0; r < botEmpty; r++) {
                    newBot.push({ value: 0, imageSrc: null });
                }
                newBot.push(...botNonZeros);
                
                const newCol = [...newTop, ...newBot];
                for (let r = 0; r < rows; r++) {
                    grid[r][c] = newCol[r];
                }
            }
        }
    }
    // Row-based shifting (Level 4, 5, 8, 9)
    else if (level === 4 || level === 5 || level === 8 || level === 9) {
        for (let r = 0; r < rows; r++) {
            const activeRow = grid[r];
            const nonZeros = activeRow.filter(cell => cell.value !== 0);
            
            if (level === 4) { // Left
                const emptyCount = cols - nonZeros.length;
                const newRow = [...nonZeros];
                for (let c = 0; c < emptyCount; c++) {
                    newRow.push({ value: 0, imageSrc: null });
                }
                grid[r] = newRow;
            } else if (level === 5) { // Right
                const emptyCount = cols - nonZeros.length;
                const newRow = [];
                for (let c = 0; c < emptyCount; c++) {
                    newRow.push({ value: 0, imageSrc: null });
                }
                newRow.push(...nonZeros);
                grid[r] = newRow;
            } else if (level === 8) { // Horizontal Center
                const leftHalf = activeRow.slice(0, 8);
                const rightHalf = activeRow.slice(8, 16);
                
                const leftNonZeros = leftHalf.filter(cell => cell.value !== 0);
                const rightNonZeros = rightHalf.filter(cell => cell.value !== 0);
                
                const newLeft = [];
                const leftEmpty = 8 - leftNonZeros.length;
                for (let c = 0; c < leftEmpty; c++) {
                    newLeft.push({ value: 0, imageSrc: null });
                }
                newLeft.push(...leftNonZeros);
                
                const newRight = [...rightNonZeros];
                const rightEmpty = 8 - rightNonZeros.length;
                for (let c = 0; c < rightEmpty; c++) {
                    newRight.push({ value: 0, imageSrc: null });
                }
                
                grid[r] = [...newLeft, ...newRight];
            } else if (level === 9) { // Horizontal Sides
                const leftHalf = activeRow.slice(0, 8);
                const rightHalf = activeRow.slice(8, 16);
                
                const leftNonZeros = leftHalf.filter(cell => cell.value !== 0);
                const rightNonZeros = rightHalf.filter(cell => cell.value !== 0);
                
                const newLeft = [...leftNonZeros];
                const leftEmpty = 8 - leftNonZeros.length;
                for (let c = 0; c < leftEmpty; c++) {
                    newLeft.push({ value: 0, imageSrc: null });
                }
                
                const newRight = [];
                const rightEmpty = 8 - rightNonZeros.length;
                for (let c = 0; c < rightEmpty; c++) {
                    newRight.push({ value: 0, imageSrc: null });
                }
                newRight.push(...rightNonZeros);
                
                grid[r] = [...newLeft, ...newRight];
            }
        }
    }
    
    return grid;
}

// Precompute the grid values and cropped images for all steps
function precomputeBoardStates() {
    boardStates = [];
    if (tileImages.length === 0) return;
    
    // Initial state (stepIndex = -1)
    let currentGridState = [];
    for (let r = 0; r < 9; r++) {
        const row = [];
        for (let c = 0; c < 16; c++) {
            const val = initialGrid[r][c];
            row.push({
                value: val,
                imageSrc: val !== 0 ? tileImages[r * 16 + c] : null
            });
        }
        currentGridState.push(row);
    }
    boardStates.push(JSON.parse(JSON.stringify(currentGridState)));
    
    // Process each step
    const selectedLevel = parseInt(levelSelect.value);
    for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        const r1 = step.start[0];
        const c1 = step.start[1];
        const r2 = step.end[0];
        const c2 = step.end[1];
        
        currentGridState[r1][c1] = { value: 0, imageSrc: null };
        currentGridState[r2][c2] = { value: 0, imageSrc: null };
        
        currentGridState = applyGravityJS(currentGridState, selectedLevel);
        boardStates.push(JSON.parse(JSON.stringify(currentGridState)));
    }
}

// Trigger solve_grid with level query/body parameters
async function solveGridWithLevel() {
    const selectedLevel = parseInt(levelSelect.value);
    try {
        const res = await fetch(`${API_URL}/api/solve_grid`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ grid: initialGrid, level: selectedLevel })
        });

        const text = await res.text();
        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            throw new Error(`Lỗi kết nối hoặc phản hồi không hợp lệ từ máy chủ (HTTP ${res.status})`);
        }

        if (!res.ok) {
            throw new Error(data.detail || "Lỗi giải grid");
        }
        steps = data.steps;

        // Render steps sidebar
        renderStepsList();

        // Warning messages
        if (data.error) {
            warningBox.style.display = "flex";
            warningText.textContent = data.error;
        } else {
            warningBox.style.display = "none";
        }

        // Adjust state
        boardStatus.textContent = data.success ? "Đã giải thành công" : "Bảng bị kẹt / Lỗi khớp cặp";
        boardStatus.className = data.success ? "badge active" : "badge";

        // Setup playback
        extractTiles(2);
        precomputeBoardStates();
        
        if (data.success && steps.length > 0) {
            playbackSection.style.display = "flex";
            totalCount.textContent = steps.length;
            resetPlayback();
        } else {
            playbackSection.style.display = "none";
            resetPlayback();
        }

    } catch (e) {
        alert("Lỗi giải bảng: " + e.message);
    }
}

// Initialize on page load
window.addEventListener("DOMContentLoaded", init);
