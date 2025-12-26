// 通用表单校验
function validateForm(formId) {
    const form = document.getElementById(formId);
    const requiredInputs = form.querySelectorAll('[required]');
    let isValid = true;

    requiredInputs.forEach(input => {
        if (!input.value.trim()) {
            alert(`${input.previousElementSibling.textContent.trim()}不能为空！`);
            input.focus();
            isValid = false;
            return false;
        }
    });

    return isValid;
}

// 日期格式化工具
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 确认提示框
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}