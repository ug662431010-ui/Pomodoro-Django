// Switch a password field between hidden and visible
function togglePasswordVisibility(id) {
    const passwordInput = document.getElementById(id);
    const toggleIcon = passwordInput.parentElement.querySelector('.toggle-password');

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.textContent = '🔒';
    } else {
        passwordInput.type = 'password';
        toggleIcon.textContent = '👁️';
    }
}
