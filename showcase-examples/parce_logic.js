pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.14.305/pdf.worker.min.js';
let uploadedFile = null;
let processedData = null;
let currentFileName = "";
let processedWidgets = [];
async function parsePptx(file) {
  const arrayBuffer = await file.arrayBuffer();
  const zip = await JSZip.loadAsync(arrayBuffer);
  let slideEntries = [];
  for (let fileName in zip.files) {
    if (fileName.startsWith("ppt/slides/slide") && fileName.endsWith(".xml")) {
      slideEntries.push(fileName);
    }
  }
  slideEntries.sort((a, b) => {
    const getNumber = name => {
      const match = name.match(/slide(\d+)\.xml$/);
      return match ? parseInt(match[1]) : 0;
    };
    return getNumber(a) - getNumber(b);
  });
  const parser = new DOMParser();
  let slides = [];
  for (let i = 0; i < slideEntries.length; i++) {
    const slideNumber = i + 1;
    const slideFile = slideEntries[i];
    const slideXmlStr = await zip.files[slideFile].async("string");
    const xmlDoc = parser.parseFromString(slideXmlStr, "application/xml");
    let shapes = [];
    let counter = 1;
    const pNamespace = "http://schemas.openxmlformats.org/presentationml/2006/main";
    const aNamespace = "http://schemas.openxmlformats.org/drawingml/2006/main";
    const spElements = xmlDoc.getElementsByTagNameNS(pNamespace, "sp");
    for (let sp of spElements) {
      let text = "";
      let txBody = sp.getElementsByTagNameNS(pNamespace, "txBody")[0];
      if (txBody) {
        let tElements = txBody.getElementsByTagNameNS(aNamespace, "t");
        let texts = [];
        for (let tElem of tElements) {
          texts.push(tElem.textContent.trim());
        }
        text = texts.join(" ").trim();
      }
      const idName = `${slideNumber}-${counter}`;
      counter++;
      shapes.push({ id: idName, name: idName, text: text });
    }
    slides.push({ slide_number: slideNumber, shapes: shapes });
  }
  return { type: "pptx", slides: slides };
}
async function parsePdf(file) {
  const arrayBuffer = await file.arrayBuffer();
  const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
  const pdf = await loadingTask.promise;
  let pages = [];
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const textContent = await page.getTextContent();
    const texts = textContent.items.map(item => item.str);
    const text = texts.join(" ").trim();
    pages.push({ page_number: i, text: text });
  }
  return { type: "pdf", pages: pages };
}
async function parseDocx(file) {
  const arrayBuffer = await file.arrayBuffer();
  const result = await mammoth.extractRawText({ arrayBuffer: arrayBuffer });
  const paragraphsRaw = result.value.split('\n');
  let paragraphs = [];
  paragraphsRaw.forEach((line, index) => {
    paragraphs.push({ paragraph_number: index + 1, text: line.trim() });
  });
  return { type: "docx", paragraphs: paragraphs };
}
function downloadJsonFile(data, fileType) {
  let counter = parseInt(localStorage.getItem('jsonFileCounter') || '1', 10);
  let filename = `data_${fileType}_${counter}.json`;
  localStorage.setItem('jsonFileCounter', counter + 1);
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const uploadButton = document.getElementById('upload-button');
const fileIcon = document.getElementById('file-icon');
const widgetContainer = document.getElementById('widget-container');
const notificationContainer = document.getElementById('notification-container');
const fileNameDisplay = document.getElementById('uploaded-file-name');
uploadArea.addEventListener('dragover', e => {
  e.preventDefault();
  uploadArea.classList.add('hover');
});
uploadArea.addEventListener('dragleave', e => {
  e.preventDefault();
  uploadArea.classList.remove('hover');
});
uploadArea.addEventListener('drop', e => {
  e.preventDefault();
  uploadArea.classList.remove('hover');
  if (e.dataTransfer.files.length) {
    handleFile(e.dataTransfer.files[0]);
  }
});
uploadArea.addEventListener('click', () => {
  fileInput.click();
});
fileInput.addEventListener('change', e => {
  if (e.target.files.length) {
    handleFile(e.target.files[0]);
  }
});
function handleFile(file) {
  const allowedMIMEs = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation'
  ];
  const extension = file.name.split('.').pop().toLowerCase();
  if (!allowedMIMEs.includes(file.type) && !['pdf','doc','docx','pptx'].includes(extension)) {
    showNotification('File type not supported. Please upload a PDF, DOC, or PPTX file.', 'error');
    return;
  }
  uploadedFile = file;
  currentFileName = file.name;
  fileNameDisplay.textContent = "Uploaded File: " + file.name;
  animateFileIcon();
  showNotification('File uploaded successfully!', 'success');
}
function animateFileIcon() {
  fileIcon.classList.add('animate');
  setTimeout(() => {
    fileIcon.classList.remove('animate');
  }, 500);
}
function showNotification(message, type) {
  const notification = document.createElement('div');
  notification.className = 'notification';
  if (type === 'error') {
    notification.style.background = '#e53935';
  }
  notification.textContent = message;
  notificationContainer.appendChild(notification);
  setTimeout(() => {
    notification.remove();
  }, 3000);
}
function renderProcessedWidgets(data) {
  widgetContainer.innerHTML = '';
  processedWidgets = [];
  const fileType = data.type;
  if (fileType === 'pptx' && data.slides) {
    data.slides.forEach(slide => {
      const widgetObj = {
        fileType: 'pptx',
        widgetType: 'slide',
        slideNumber: slide.slide_number,
        shapes: slide.shapes,
        fileName: currentFileName
      };
      processedWidgets.push(widgetObj);
      const widgetEl = createWidgetElement(widgetObj, `Slide ${slide.slide_number}`);
      widgetContainer.appendChild(widgetEl);
    });
  } else if (fileType === 'pdf' && data.pages) {
    data.pages.forEach(page => {
      let paragraphs = page.text.split(/\n+/).filter(p => p.trim() !== '');
      if (paragraphs.length === 0) {
        paragraphs = [page.text];
      }
      paragraphs.forEach((para, index) => {
        const widgetObj = {
          fileType: 'pdf',
          widgetType: 'paragraph',
          pageNumber: page.page_number,
          paragraphIndex: index + 1,
          text: para,
          fileName: currentFileName
        };
        processedWidgets.push(widgetObj);
        const title = `Page ${page.page_number} - Paragraph ${index + 1}`;
        const widgetEl = createWidgetElement(widgetObj, title);
        widgetContainer.appendChild(widgetEl);
      });
    });
  } else if (fileType === 'docx' && data.paragraphs) {
    data.paragraphs.forEach(para => {
      const widgetObj = {
        fileType: 'docx',
        widgetType: 'paragraph',
        paragraphNumber: para.paragraph_number,
        text: para.text,
        fileName: currentFileName
      };
      processedWidgets.push(widgetObj);
      const title = `Paragraph ${para.paragraph_number}`;
      const widgetEl = createWidgetElement(widgetObj, title);
      widgetContainer.appendChild(widgetEl);
    });
  }
}
function createWidgetElement(widgetObj, titleText) {
  const widgetEl = document.createElement('div');
  widgetEl.className = 'widget';
  const title = document.createElement('h2');
  title.textContent = titleText;
  widgetEl.appendChild(title);
  const content = document.createElement('div');
  if (widgetObj.widgetType === 'slide' && widgetObj.shapes) {
    widgetObj.shapes.forEach(shape => {
      const p = document.createElement('p');
      p.textContent = shape.text;
      content.appendChild(p);
    });
  } else if (widgetObj.widgetType === 'paragraph') {
    const p = document.createElement('p');
    p.textContent = widgetObj.text;
    content.appendChild(p);
  }
  widgetEl.appendChild(content);
  const btnContainer = document.createElement('div');
  const addBtn = document.createElement('button');
  addBtn.textContent = 'Add to Log';
  addBtn.className = 'btn';
  addBtn.addEventListener('click', () => {
    addWidgetToLog(widgetObj);
    widgetEl.remove();
  });
  btnContainer.appendChild(addBtn);
  const removeBtn = document.createElement('button');
  removeBtn.textContent = 'Remove';
  removeBtn.className = 'btn';
  removeBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to remove this widget?')) {
      widgetEl.remove();
    }
  });
  btnContainer.appendChild(removeBtn);
  widgetEl.appendChild(btnContainer);
  return widgetEl;
}
function addWidgetToLog(widgetObj) {
  let widgetLog = JSON.parse(localStorage.getItem('widgetLog')) || [];
  widgetLog.push(widgetObj);
  localStorage.setItem('widgetLog', JSON.stringify(widgetLog));
  showNotification('Widget added to log.', 'success');
}
uploadButton.addEventListener('click', async () => {
  if (!uploadedFile) {
    showNotification('Please upload a valid file before processing.', 'error');
    return;
  }
  showNotification('Processing file...', 'success');
  const extension = uploadedFile.name.split('.').pop().toLowerCase();
  try {
    if (extension === 'pptx') {
      processedData = await parsePptx(uploadedFile);
    } else if (extension === 'pdf') {
      processedData = await parsePdf(uploadedFile);
    } else if (extension === 'docx' || extension === 'doc') {
      processedData = await parseDocx(uploadedFile);
    } else {
      showNotification('Unsupported file type.', 'error');
      return;
    }
    downloadJsonFile(processedData, processedData.type);
    renderProcessedWidgets(processedData);
  } catch (error) {
    showNotification('An error occurred while processing the file.', 'error');
  }
});
function loadWidgetLog() {
  const widgetLogContainer = document.getElementById('widget-log');
  widgetLogContainer.innerHTML = '';
  let widgetLog = JSON.parse(localStorage.getItem('widgetLog')) || [];
  if (widgetLog.length === 0) {
    widgetLogContainer.textContent = 'No saved widgets.';
    return;
  }
  widgetLog.forEach((widgetObj, index) => {
    const widgetEl = document.createElement('div');
    widgetEl.className = 'widget';
    let titleText = '';
    if (widgetObj.fileType === 'pptx' && widgetObj.widgetType === 'slide') {
      titleText = `Slide ${widgetObj.slideNumber} (File: ${widgetObj.fileName})`;
    } else if (widgetObj.fileType === 'pdf' && widgetObj.widgetType === 'paragraph') {
      titleText = `Page ${widgetObj.pageNumber} - Paragraph ${widgetObj.paragraphIndex} (File: ${widgetObj.fileName})`;
    } else if (widgetObj.fileType === 'docx' && widgetObj.widgetType === 'paragraph') {
      titleText = `Paragraph ${widgetObj.paragraphNumber} (File: ${widgetObj.fileName})`;
    }
    const title = document.createElement('h2');
    title.textContent = titleText;
    widgetEl.appendChild(title);
    const content = document.createElement('div');
    if (widgetObj.widgetType === 'slide' && widgetObj.shapes) {
      widgetObj.shapes.forEach(shape => {
        const p = document.createElement('p');
        p.textContent = shape.text;
        content.appendChild(p);
      });
    } else if (widgetObj.widgetType === 'paragraph') {
      const p = document.createElement('p');
      p.textContent = widgetObj.text;
      content.appendChild(p);
    }
    widgetEl.appendChild(content);
    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = 'Delete Log';
    deleteBtn.className = 'btn';
    deleteBtn.addEventListener('click', () => {
      if (confirm('Are you sure you want to delete this log?')) {
        widgetLog.splice(index, 1);
        localStorage.setItem('widgetLog', JSON.stringify(widgetLog));
        loadWidgetLog();
        showNotification('Log deleted.', 'success');
      }
    });
    widgetEl.appendChild(deleteBtn);
    widgetLogContainer.appendChild(widgetEl);
  });
}
document.getElementById('home-tab').addEventListener('click', e => {
  e.preventDefault();
  document.getElementById('home-section').style.display = 'block';
  document.getElementById('log-section').style.display = 'none';
});
document.getElementById('log-tab').addEventListener('click', e => {
  e.preventDefault();
  document.getElementById('home-section').style.display = 'none';
  document.getElementById('log-section').style.display = 'block';
  loadWidgetLog();
});
