// Insect Annotation Tool JavaScript

let canvas, ctx;
let currentImage = null;
let currentImageName = "";
let annotations = [];
let selectedAnnotation = -1;
let isDrawing = false;
let startX, startY, endX, endY;
let scale = 1;
let offsetX = 0,
  offsetY = 0;
let classes = [];
let imageWidth = 0,
  imageHeight = 0;

// Initialize the application
document.addEventListener("DOMContentLoaded", function () {
  canvas = document.getElementById("annotationCanvas");
  ctx = canvas.getContext("2d");

  setupEventListeners();
  loadClasses();
});

function setupEventListeners() {
  // Canvas events
  canvas.addEventListener("mousedown", onMouseDown);
  canvas.addEventListener("mousemove", onMouseMove);
  canvas.addEventListener("mouseup", onMouseUp);
  canvas.addEventListener("click", onCanvasClick);

  // Mode change events
  document.querySelectorAll('input[name="mode"]').forEach((radio) => {
    radio.addEventListener("change", function () {
      updateCanvasCursor();
    });
  });

  // Keyboard shortcuts
  document.addEventListener("keydown", function (e) {
    if (e.key === "Delete" && selectedAnnotation >= 0) {
      deleteSelected();
    } else if (e.key === "Escape") {
      selectedAnnotation = -1;
      redrawCanvas();
    }
  });
}

function updateCanvasCursor() {
  const mode = document.querySelector('input[name="mode"]:checked').value;
  canvas.className = mode === "select" ? "select-mode" : "";
}

function loadImage(imageName) {
  currentImageName = imageName;
  document.getElementById(
    "currentImageName"
  ).innerHTML = `<i class="fas fa-image"></i> ${imageName}`;

  // Update active image in list
  document.querySelectorAll(".image-item").forEach((item) => {
    item.classList.remove("active");
  });
  event.target.closest(".image-item").classList.add("active");

  // Load image info and annotations
  fetch(`/get_image_info/${imageName}`)
    .then((response) => response.json())
    .then((data) => {
      imageWidth = data.width;
      imageHeight = data.height;
      annotations = data.annotations || [];
      classes = data.classes || [];

      updateClassSelect();
      loadImageToCanvas(imageName);
    })
    .catch((error) => {
      console.error("Error loading image info:", error);
      showAlert("เกิดข้อผิดพลาดในการโหลดข้อมูลรูปภาพ", "danger");
    });
}

function loadImageToCanvas(imageName) {
  const img = new Image();
  img.onload = function () {
    currentImage = img;

    // Calculate canvas size to fit the container while maintaining aspect ratio
    const container = document.getElementById("canvasContainer");
    const maxWidth = container.clientWidth - 20;
    const maxHeight = Math.min(600, window.innerHeight * 0.6);

    const aspectRatio = img.width / img.height;
    let canvasWidth, canvasHeight;

    if (img.width > img.height) {
      canvasWidth = Math.min(maxWidth, img.width);
      canvasHeight = canvasWidth / aspectRatio;
    } else {
      canvasHeight = Math.min(maxHeight, img.height);
      canvasWidth = canvasHeight * aspectRatio;
    }

    canvas.width = canvasWidth;
    canvas.height = canvasHeight;

    scale = canvasWidth / img.width;

    redrawCanvas();
    updateAnnotationList();
  };
  img.src = `/images/${imageName}`;
}

function redrawCanvas() {
  if (!currentImage) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw image
  ctx.drawImage(currentImage, 0, 0, canvas.width, canvas.height);

  // Draw annotations
  annotations.forEach((ann, index) => {
    drawAnnotation(ann, index === selectedAnnotation);
  });
}

function drawAnnotation(annotation, isSelected = false) {
  const x = (annotation.x_center - annotation.width / 2) * canvas.width;
  const y = (annotation.y_center - annotation.height / 2) * canvas.height;
  const width = annotation.width * canvas.width;
  const height = annotation.height * canvas.height;

  // Set style based on selection
  ctx.strokeStyle = isSelected ? "#ff0000" : "#00ff00";
  ctx.lineWidth = isSelected ? 3 : 2;
  ctx.fillStyle = isSelected ? "rgba(255, 0, 0, 0.2)" : "rgba(0, 255, 0, 0.2)";

  // Draw rectangle
  ctx.fillRect(x, y, width, height);
  ctx.strokeRect(x, y, width, height);

  // Draw class label
  if (annotation.class_id < classes.length) {
    const className = classes[annotation.class_id];
    ctx.fillStyle = isSelected ? "#ff0000" : "#00ff00";
    ctx.font = "14px Arial";
    ctx.fillText(className, x, y - 5);
  }
}

function onMouseDown(e) {
  const mode = document.querySelector('input[name="mode"]:checked').value;
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  if (mode === "draw") {
    isDrawing = true;
    startX = x / canvas.width;
    startY = y / canvas.height;
  } else if (mode === "select") {
    selectAnnotation(x, y);
  }
}

function onMouseMove(e) {
  if (!isDrawing) return;

  const rect = canvas.getBoundingClientRect();
  endX = (e.clientX - rect.left) / canvas.width;
  endY = (e.clientY - rect.top) / canvas.height;

  redrawCanvas();

  // Draw current rectangle being drawn
  const x = Math.min(startX, endX) * canvas.width;
  const y = Math.min(startY, endY) * canvas.height;
  const width = Math.abs(endX - startX) * canvas.width;
  const height = Math.abs(endY - startY) * canvas.height;

  ctx.strokeStyle = "#0080ff";
  ctx.lineWidth = 2;
  ctx.fillStyle = "rgba(0, 128, 255, 0.2)";
  ctx.fillRect(x, y, width, height);
  ctx.strokeRect(x, y, width, height);
}

function onMouseUp(e) {
  if (!isDrawing) return;

  isDrawing = false;

  const rect = canvas.getBoundingClientRect();
  endX = (e.clientX - rect.left) / canvas.width;
  endY = (e.clientY - rect.top) / canvas.height;

  // Create annotation if rectangle is large enough
  const width = Math.abs(endX - startX);
  const height = Math.abs(endY - startY);

  if (width > 0.01 && height > 0.01) {
    const classId = parseInt(document.getElementById("classSelect").value);
    const annotation = {
      class_id: classId,
      x_center: (startX + endX) / 2,
      y_center: (startY + endY) / 2,
      width: width,
      height: height,
    };

    annotations.push(annotation);
    updateAnnotationList();
    redrawCanvas();
  }
}

function onCanvasClick(e) {
  const mode = document.querySelector('input[name="mode"]:checked').value;
  if (mode === "select") {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    selectAnnotation(x, y);
  }
}

function selectAnnotation(x, y) {
  const clickX = x / canvas.width;
  const clickY = y / canvas.height;

  selectedAnnotation = -1;

  for (let i = annotations.length - 1; i >= 0; i--) {
    const ann = annotations[i];
    const left = ann.x_center - ann.width / 2;
    const right = ann.x_center + ann.width / 2;
    const top = ann.y_center - ann.height / 2;
    const bottom = ann.y_center + ann.height / 2;

    if (
      clickX >= left &&
      clickX <= right &&
      clickY >= top &&
      clickY <= bottom
    ) {
      selectedAnnotation = i;
      break;
    }
  }

  updateAnnotationList();
  redrawCanvas();
}

function updateAnnotationList() {
  const listContainer = document.getElementById("annotationList");
  listContainer.innerHTML = "";

  if (annotations.length === 0) {
    listContainer.innerHTML =
      '<p class="text-muted small">ยังไม่มี annotation</p>';
    return;
  }

  annotations.forEach((ann, index) => {
    const className =
      ann.class_id < classes.length ? classes[ann.class_id] : "Unknown";
    const item = document.createElement("div");
    item.className = `annotation-item ${
      index === selectedAnnotation ? "selected" : ""
    }`;
    item.innerHTML = `
            <strong>${className}</strong><br>
            <small>Center: (${(ann.x_center * 100).toFixed(1)}%, ${(
      ann.y_center * 100
    ).toFixed(1)}%)</small><br>
            <small>Size: ${(ann.width * 100).toFixed(1)}% × ${(
      ann.height * 100
    ).toFixed(1)}%</small>
        `;
    item.onclick = () => {
      selectedAnnotation = index;
      updateAnnotationList();
      redrawCanvas();
    };
    listContainer.appendChild(item);
  });
}

function updateClassSelect() {
  const select = document.getElementById("classSelect");
  select.innerHTML = "";

  classes.forEach((className, index) => {
    const option = document.createElement("option");
    option.value = index;
    option.textContent = className;
    select.appendChild(option);
  });
}

function saveAnnotations() {
  if (!currentImageName) {
    showAlert("กรุณาเลือกรูปภาพก่อน", "warning");
    return;
  }

  const data = {
    image_name: currentImageName,
    annotations: annotations,
  };

  fetch("/save_annotation", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showAlert("บันทึก annotation เรียบร้อยแล้ว", "success");
      } else {
        showAlert("เกิดข้อผิดพลาดในการบันทึก", "danger");
      }
    })
    .catch((error) => {
      console.error("Error saving annotations:", error);
      showAlert("เกิดข้อผิดพลาดในการบันทึก", "danger");
    });
}

function clearAnnotations() {
  if (confirm("คุณแน่ใจหรือไม่ที่จะลบ annotation ทั้งหมด?")) {
    annotations = [];
    selectedAnnotation = -1;
    updateAnnotationList();
    redrawCanvas();
  }
}

function deleteSelected() {
  if (selectedAnnotation >= 0) {
    annotations.splice(selectedAnnotation, 1);
    selectedAnnotation = -1;
    updateAnnotationList();
    redrawCanvas();
  }
}

function zoomIn() {
  scale *= 1.2;
  applyZoom();
}

function zoomOut() {
  scale /= 1.2;
  applyZoom();
}

function resetZoom() {
  scale = 1;
  applyZoom();
}

function applyZoom() {
  if (!currentImage) return;

  const newWidth = currentImage.width * scale;
  const newHeight = currentImage.height * scale;

  canvas.width = newWidth;
  canvas.height = newHeight;

  redrawCanvas();
}

// Modal functions
function showUploadModal() {
  const modal = new bootstrap.Modal(document.getElementById("uploadModal"));
  modal.show();
}

function showClassModal() {
  loadClassList();
  const modal = new bootstrap.Modal(document.getElementById("classModal"));
  modal.show();
}

function uploadFiles() {
  const fileInput = document.getElementById("fileInput");
  const files = fileInput.files;

  if (files.length === 0) {
    showAlert("กรุณาเลือกไฟล์", "warning");
    return;
  }

  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  fetch("/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.uploaded_files && data.uploaded_files.length > 0) {
        showAlert(
          `อัพโหลดไฟล์สำเร็จ ${data.uploaded_files.length} ไฟล์`,
          "success"
        );
        setTimeout(() => location.reload(), 1000);
      } else {
        showAlert("ไม่สามารถอัพโหลดไฟล์ได้", "danger");
      }
    })
    .catch((error) => {
      console.error("Error uploading files:", error);
      showAlert("เกิดข้อผิดพลาดในการอัพโหลด", "danger");
    });

  bootstrap.Modal.getInstance(document.getElementById("uploadModal")).hide();
}

function loadClasses() {
  fetch("/get_classes")
    .then((response) => response.json())
    .then((data) => {
      classes = data.classes;
      updateClassSelect();
    })
    .catch((error) => {
      console.error("Error loading classes:", error);
    });
}

function loadClassList() {
  const container = document.getElementById("classList");
  container.innerHTML = "";

  classes.forEach((className) => {
    const item = document.createElement("div");
    item.className = "class-item";
    item.innerHTML = `
            <span>${className}</span>
            <button class="btn btn-danger btn-sm btn-delete-class" onclick="deleteClass('${className}')">
                <i class="fas fa-trash"></i>
            </button>
        `;
    container.appendChild(item);
  });
}

function addClass() {
  const input = document.getElementById("newClassName");
  const className = input.value.trim();

  if (!className) {
    showAlert("กรุณาใส่ชื่อคลาส", "warning");
    return;
  }

  fetch("/add_class", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ class_name: className }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        classes = data.classes;
        updateClassSelect();
        loadClassList();
        input.value = "";
        showAlert("เพิ่มคลาสสำเร็จ", "success");
      } else {
        showAlert(data.error || "เกิดข้อผิดพลาด", "danger");
      }
    })
    .catch((error) => {
      console.error("Error adding class:", error);
      showAlert("เกิดข้อผิดพลาด", "danger");
    });
}

function deleteClass(className) {
  if (!confirm(`คุณแน่ใจหรือไม่ที่จะลบคลาส "${className}"?`)) {
    return;
  }

  fetch("/delete_class", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ class_name: className }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        classes = data.classes;
        updateClassSelect();
        loadClassList();
        showAlert("ลบคลาสสำเร็จ", "success");
      } else {
        showAlert(data.error || "เกิดข้อผิดพลาด", "danger");
      }
    })
    .catch((error) => {
      console.error("Error deleting class:", error);
      showAlert("เกิดข้อผิดพลาด", "danger");
    });
}

function exportDataset() {
  fetch("/export_dataset")
    .then((response) => response.json())
    .then((data) => {
      let message = `สถิติข้อมูล:\n`;
      message += `รูปภาพทั้งหมด: ${data.total_images}\n`;
      message += `รูปที่ annotate แล้ว: ${data.annotated_images}\n`;
      message += `จำนวน annotation: ${data.total_annotations}\n`;
      message += `จำนวนคลาส: ${data.total_classes}\n\n`;
      message += `การกระจายตามคลาส:\n`;

      for (const [className, count] of Object.entries(
        data.class_distribution
      )) {
        message += `${className}: ${count}\n`;
      }

      alert(message);
    })
    .catch((error) => {
      console.error("Error exporting dataset:", error);
      showAlert("เกิดข้อผิดพลาดในการส่งออกข้อมูล", "danger");
    });
}

function showAlert(message, type = "info") {
  const alertContainer = document.createElement("div");
  alertContainer.className = `alert alert-${type} alert-custom alert-dismissible fade show`;
  alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

  document.body.appendChild(alertContainer);

  setTimeout(() => {
    if (alertContainer.parentNode) {
      alertContainer.parentNode.removeChild(alertContainer);
    }
  }, 5000);
}
