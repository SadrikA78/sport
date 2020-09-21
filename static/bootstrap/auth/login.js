$(function() {
    $('.logo').on('click', function (e) {
        $('.units_list.modal')
            .modal({
                selector: {
                    close: '.close',
                    approve: '.actions .approve',
                    deny: '.actions .cancel'
                },
                setting: {
                    transition: 'scale',
                    keyboardShortcuts: true,
                },
            });
          //  .modal('show');
    });

    $('.login-as').on('click', function (e) {
        $(this).hide().next('.login').show();

        setTimeout(function () {
            $('.login input').focus();
        }, 100);
    });

    $('.message .close').on('click', function (e) {
        $(this)
            .closest('.message')
            .transition('fade');
    });

    var errors_login = $('.login-errors');

    if (errors_login.find('p').text() != '') {
        setTimeout(function () {
            errors_login
                .css({'top': (-errors_login.height() - 30) + 'px', 'opacity': 0})
                .show()
                .animate({'top': 20, 'opacity': 1}, 200);
        }, 10);
    }
});