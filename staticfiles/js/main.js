// فعال کردن tooltip‌ها
document.addEventListener('DOMContentLoaded', function() {
    // هایلایت لینک فعال در نوار ناوبری
    const currentUrl = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentUrl) {
            link.classList.add('active');
        }
    });
    
    // در صورت نیاز می‌توانید اسکریپت‌های دیگر را اینجا اضافه کنید
});

document.getElementById('edit-profile-btn').addEventListener('click', function (e) {
  e.preventDefault();
  fetch('/edit-profile-modal/', {
    method: 'GET',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
    },
  })
    .then(response => {
      if (response.ok) {
        return response.text();
      }
      throw new Error('خطا در دریافت اطلاعات');
    })
    .then(html => {
      document.getElementById('edit-profile-modal-content').innerHTML = html;
      new bootstrap.Modal(document.getElementById('editProfileModal')).show();
    })
    .catch(error => {
      console.error(error);
    });
});