$(document).ready(function () {

    //Cuando se cierre el navegador o pestaña utilizamos ajax para notificarselo a django.
    // FIXME: No se puede distinguir si se cierra, se refresca o se navega
    // $(window).on('beforeunload', function () {
    //     doAjaxBeforeUnloadEnabled = false;
    //     jQuery.ajax({
    //         url: "/logout/",
    //         success: function (a) {
    //             console.debug("Ajax call finished");
    //         },
    //     });
    // });

    // este metodo se ejecuta cuando el DOM esta listo
    $(function () {
        //Comprobamos que esté en la pantalla de juego
        var gameViewLayout = $('.game-view')
        if (0 < gameViewLayout.length) {
            getCurrentEventsMessages()
        }
    })

    //Añadimos un fadein para el onload de la pagina
    $('body main').css('display', 'none');
    // $('body main').fadeIn(300);
    $('body main').stop().fadeTo('slow', 1);

    //Funciones para el custom dropdown
    $(".dropdown-el, .select-field").click(function (e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).toggleClass("expanded");
    });
    $(".dropdown-el, .select-field .input-label").click(function (e) {
        $("#" + $(e.target).attr("for")).prop("checked", true)
        var selectContainer = $(this).parents(".select-field")
        var lbl = selectContainer.parent().siblings(".col-form-label")
        lbl.addClass("placeholder-hide")
    });


    $(".rounded-input-theme .textInput").on("keypress", function () {
        var lbl = $(this).parent().siblings(".col-form-label")
        if (placeholderActive($(this))) {
            lbl.addClass("placeholder-hide")
        }
    });
    $(".rounded-input-theme .textInput").on("keyup", function () {
        if (!$(this).val()) {
            var lbl = $(this).parent().siblings(".col-form-label")
            lbl.removeClass("placeholder-hide")
        }
    });

    // Botón de seleccion del listado
    $(".item-select-button").on("click", function () {

        var item_id = $(this).data('item-id')
        $(".card-deck input[name='item-selected']").val(item_id)
    });

    //Input file
    $('#file-upload').change(function () {
        var filename = $('#file-upload').val().split('\\').pop();
        $('.custom-file-upload.file-name').text(filename)
    })
    $('#custom-file-upload').click(function () {
        $('#file-upload').click()
    }).show();

    //Funcion para la validación de una clave
    $('.js-validate-key-code').on("click", function () {
        $('.messages-wrapper').empty()
        validateKeyCode()
    });

    $('.show-details-case-btn').on("click", function () {
        if (null == $(this).data('case-finish-date')) {
            var group_game_case_id = $(this).data('item-id')
            var case_id = $(this).data('case-id')
            var case_start_date = $(this).data('case-start-date')
            if (null != case_start_date && '' != case_start_date && 'none' != case_start_date.toLocaleLowerCase()) {
                $('#startCaseBtn').html('Continuar caso')
            }
            $.ajax({
                headers: {"X-CSRFToken": getcsrftoken()},
                url: '/game/ajax/get_case_title/',
                data: {'case_id': case_id},
                cache: false,
                type: 'POST',
                success: function (data) {
                    if ('ok' === data['status']) {
                        $('#caseStoryTitle').html(data['title'])
                    }
                }
            }).promise().done(function () {
                generateCaseDockerContainer(group_game_case_id, case_id)
                getStoryMessageContent(case_id, null)
            });
        }
    });

    $('.next-event-btn').on('click', function () {
        addPlayerResponse()
    })

    $('#storyModalDialog').on('hidden.bs.modal', function (e) {
        continueStory()
    })
    $('#storyModalDialog .next-story-btn').on("click", function () {
        $('#storyModalDialog').modal('hide')
    })

    $('.case-ranking.table-panel .table tr.selectable').on('click', function () {
        var case_id = $(this).data('case-id')
        var group_id = $(this).data('group-id')
        var form = $('.case-ranking.table-panel .table-selectable-form')
        var url = "/game/case_detail/case_id/group_id/".replace('case_id', case_id).replace('group_id', group_id)
        form.attr('action', url)
        form.submit()
    })

    $('.event-table.table-panel .table tr.selectable').on('click', function () {
        var event_id = $(this).data('event-id')
        var group_id = $(this).data('group-id')
        var form = $('.event-table.table-panel .table-selectable-form')
        var url = "/game/event_detail/event_id/group_id/".replace('event_id', event_id).replace('group_id', group_id)
        form.attr('action', url)
        form.submit()
    })

    $('.toast').toast('show')
    $('[data-toggle="popover"]').popover()
    $('.popover-dismiss').popover({
        trigger: 'focus'
    })

    $('.player-rating-btn').on('click', function () {
        var gartifactiId = $(this).data('gartifact-info-id')
        responsePlayerLike(gartifactiId)
    })

    $('.users-management-view').on('change', '.user-group-table .user-group-select-combo', function () {
        var select = $(this)
        var groupId = select.val()
        var userId = select.data('user-id')
        var tableWrapper = $('.user-group-table')
        var courseId = tableWrapper.data('course-id')
        var year = tableWrapper.data('year')
        var username = select.data('username')
        usersGroupChanged(groupId, userId, courseId, year, username)
    })

    $('.users-management-view').on("click", '#newGroupModal .new-group-btn', function () {
        var modal = $('#newGroupModal')
        var groupName = modal.find('#group-name').val()
        var userId = modal.data('user-id')
        var table = $('.group-config-form-wrapper .user-group-table')
        var courseId = table.data('course-id')
        var year = table.data('year')
        modal.modal('hide')

        createNewGroup(groupName, userId, courseId, year)
    })

    $('.users-upload-course-select-btn').on('click', function () {
        var courseId = $('#id_courses').val()
        var year = $('#id_year').val()
        usersGroupCourseSelected(courseId, year)
        if (courseId && year) {

            var processingMsg = $(this).data('processing')
            if (processingMsg) {
                $(this).html('<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span>' + processingMsg)
            }
        }
    })

    hidePlaceholderOnTextInputWithInitialValue();

    setChatMsgCounterRefreshInterval()
});

// var doAjaxBeforeUnloadEnabled = true;

$(document).click(function () {
    $(".dropdown-el, .select-field").removeClass("expanded");
});

//Añadimos fadeout para un cambio entre paginas más fluida
window.addEventListener("beforeunload", function (event) {
    $('body main').stop().fadeTo('slow', 0);
});


function placeholderActive(element) {
    return element.attr('placeholder') && !element.val()
}

function hidePlaceholderOnTextInputWithInitialValue() {
    var textInputField = $(".textInput")
    if (textInputField.val) {
        var lbl = textInputField.parent().siblings(".col-form-label")
        lbl.addClass("placeholder-hide")
    }
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function validateKeyCode() {
    $.ajax({
        url: 'ajax/validate_key_code/',
        data: $(".key-code-form").serialize(),
        cache: false,
        type: 'POST',
        success: function (data) {
            $('#id_key_code').removeClass('is-invalid')
            $('#error_1_id_key_code').remove();
            if (data['status'] == "ok") {
                showKeyCommentDialog(data['group_artifact_info_id'], data['artifact_name'], data['score'], data['key_code'])
            } else {
                errorMsg = data['error']
                $('#id_key_code').addClass('is-invalid')
                $('#id_key_code').parent()//
                    .append($('<p id="error_1_id_key_code" class="invalid-feedback"></p>').append($('<strong></strong>').text(errorMsg)))
            }
        }
    });
}

function generateCaseDockerContainer(group_game_case_id, case_id) {
    $.ajax({
        headers: {"X-CSRFToken": getcsrftoken()},
        url: '/game/ajax/generate_container/',
        type: "POST",
        cache: false,
        dataType: "json",
        data: {'group_game_case_id': group_game_case_id, 'case_id': case_id},
        success: function (data) {

            var status = data['container_status']
            //Si la creación no ha dado error activamos el botón para seleccionar el caso
            if ('ok' === status) {
                var btn = $('#caseStoryModalDialog').find('.start-case-btn')
                btn.removeClass('loading')
                btn.removeAttr('data-toggle')
                btn.removeAttr('title')
                btn.prop("disabled", false);
                $(btn).attr('data-item-id', group_game_case_id)
                $(btn).attr('data-case-id', case_id)
            }
        }
    });
}

function getcsrftoken() {
    return getCookie('csrftoken');
}

function getStoryMessageContent(case_id, story_id, delay) {
    if (null == delay) delay = 0;
    $.ajax({
        headers: {"X-CSRFToken": getcsrftoken()},
        url: '/game/ajax/get_story_message/',
        type: "POST",
        cache: false,
        dataType: "json",
        data: {'case_id': case_id, 'story_id': story_id},
        async: false,
        success: function (data) {

            if ('ok' === data['status']) {

                if (true == data['show_popup']) {
                    var dialog = $('#caseStoryModalDialog')
                    if (0 == dialog.length) {
                        dialog = $('#storyModalDialog')
                    }
                    var content = dialog.find('.message-content')
                    content.empty()
                    if (true == data['is_embebed']) {
                        content.append("<embed src=" + data['message_url'] + " class='embed-pdf' alt='details' pluginspage='http://www.adobe.com/products/acrobat/readstep2.html'>")
                    } else {
                        content.append(data['message_text'])
                    }

                    if (null == delay) {
                        delay = 0
                    }
                    setTimeout(function () {

                        dialog.modal('show')
                    }, delay)
                } else if (true == data['show_chat']) {

                    setTimeout(function () {

                        addPendingChatMessages(data['chat_messages'], true)
                    }, delay)
                }
            }
        }
    });
}

function addPlayerResponse() {
    $.ajax({
        url: 'ajax/add_response/',
        data: $(".comment-form").serialize(),
        cache: false,
        type: 'POST',
        success: function (data) {
            if (data['status'] == "ok") {
                $('#id_key_code').val("")
                $('#id_comment').val("")
                $('#keyCommentModalDialog').modal('hide')
                var event = data['event']
                if (null != event) {
                    var showNewEventMessages = true
                    var group_game_case_id = data['group_game_case_id']
                    var endEventStory = data['end_event_story']
                    if (null != endEventStory) {
                        showNewEventMessages = false
                        var case_id = data['case_id']
                        getStoryMessageContent(case_id, endEventStory)
                    }
                    unlockEvents(group_game_case_id, event, showNewEventMessages)
                } else {
                    add_messages_to_view("success", data['message'])
                }
            }
        }
    });
}

var pendingEventStories = [];
var pendingChatMessages = [];

function addPendingEventStories(events, continueWithTheStory) {
    if (null != events && 0 < events.length) {
        for (var index in events) {
            if(events[index].story_id != undefined){
                pendingEventStories.push(events[index])
            }
        }
    }
    if (continueWithTheStory) {
        continueStory()
    }
}

function addPendingChatMessages(messages, continueWithTheStory) {
    if (null != messages && 0 < messages.length) {
        for (var index in messages) {
            pendingChatMessages.push(messages[index])
        }
    }
    if (continueWithTheStory) {
        continueStory()
    }
}

function unlockEvents(group_game_case_id, event, showNewEventMessages) {
    $.ajax({
        headers: {"X-CSRFToken": getcsrftoken()},
        url: 'ajax/unlock_events/',
        data: {'group_game_case_id': group_game_case_id, 'event': event},
        cache: false,
        type: 'POST',
        success: function (data) {
            if (data['status'] == "ok") {
                var events = data['next_events']
                if (null != events && 0 < events.length) {
                    addPendingEventStories(events, showNewEventMessages)
                    refreshClueBar()
                } else {
                    $('.game-message').empty()
                    $('.game-message').append(data['game_msg'])

                    var willStoryDialogClose = new Promise(
                        function (resolve, reject) {
                            var is_show = $('#storyModalDialog').hasClass('.show')

                            if (!is_show) {
                                resolve(is_show); // fulfilled
                            } else {
                                var reason = new Error('Se esta visualizando el modal');
                                reject(reason); // reject
                            }
                        }
                    );
                    var showMsg = function () {
                        willStoryDialogClose.then(function (value) {
                            $('#gameModalDialog').modal('show')
                        })
                    }
                    showMsg()
                }
            }
        }
    });
}

function continueStory() {

    if (0 < pendingChatMessages.length) {
        var msg = pendingChatMessages.shift()
        refreshChatMessages(msg.id, null, null, msg.delay)
    }
    if (0 < pendingEventStories.length) {
        var ev = pendingEventStories.shift()
        getStoryMessageContent(ev.case_id, ev.story_id, ev.delay)
    }
}

function refreshClueBar() {
    $.ajax({
        headers: {"X-CSRFToken": getcsrftoken()},
        url: '',
        cache: false,
        type: 'POST',
        success: function (data) {
            $('.clue-wrapper').html(data)
        }
    });
}

function refreshChatMessages(message_id, conversation_id, contact_id, delay) {
    $.ajax({
        headers: {"X-CSRFToken": getcsrftoken()},
        url: '',
        cache: false,
        data: {'message_id': message_id, 'conversation_id': conversation_id, 'contact_id': contact_id, 'delay': delay},
        type: 'POST',
        success: function (data) {
            setTimeout(function () {
                $('#collapseGameChat').html(data)
                $('#collapseGameChat').collapse('show')
                $('#collapseConversationChat').collapse('show')
                chat_scroll_down()
                continueStory()
            }, delay)
        }
    });
}

function getCurrentEventsMessages() {
    $.ajax({
        headers: {"X-CSRFToken": getcsrftoken()},
        url: 'ajax/get_current_events_messages/',
        cache: false,
        type: 'POST',
        success: function (data) {
            if (data['status'] == "ok") {
                var events = data['events']
                if (null != events && 0 < events.length) {
                    addPendingEventStories(events, true)
                }
            }
        }
    });
}

function add_messages_to_view(level, message) {
    $.ajax({
        headers: {"X-CSRFToken": getcsrftoken()},
        url: '/ajax/add_messages_to_view/',
        cache: false,
        type: 'POST',
        data: {'level': level, 'message': message},
        success: function (data) {
            $('.messages-wrapper').html(data)
            $('.toast').toast('show')
        }
    });
}

function send_chat_message(cid) {
    $.ajax({
        headers: {"X-CSRFToken": getcsrftoken()},
        url: 'ajax/send_chat_message/',
        data: {'msg': $('.chat-message-field').val(), 'conversation_id': cid},
        cache: false,
        type: 'POST',
        success: function (data) {

            if (data['status'] == "ok") {
                refreshChatMessages(null, cid, null, 0)

                validate_chat_message(cid, data['msgid'])
            }
        }
    });
}

function validate_chat_message(cid, cmid) {
    $.ajax({
        headers: {"X-CSRFToken": getcsrftoken()},
        url: 'ajax/validate_chat_message/',
        data: {'chat_message_id': cmid},
        cache: false,
        type: 'POST',
        success: function (data) {

            if (data['status'] == "error") {
                refreshChatMessages(null, cid, null, 0)
            } else {
                showKeyCommentDialog(data['group_artifact_info_id'], data['artifact_name'], data['score'], data['key_code'])
            }
        }
    });
}

function chat_scroll_down() {

    var n = $('.msg_card_body').height();
    $('.msg_card_body').animate({scrollTop: n}, 500);
}

function showKeyCommentDialog(group_artifact_info_id, artifact_name, score, key_code) {
    $('#id_group_artifact_info').val(group_artifact_info_id)
    $('#comment-dialog-artifact-name').text(artifact_name)
    $('#comment-dialog-score').text(score)
    $('#id_comment_key_code').val(key_code)
    $('#keyCommentModalDialog').modal('show')
}


function setChatMsgCounterRefreshInterval() {

    if (0 < $('.chat-btn').length) {
        setInterval(checkNewChatMessages, 5000)
    }
}

function checkNewChatMessages() {
    $.ajax({
        url: 'ajax/get_unread_message/',
        cache: false,
        success: function (data) {

            if (data['status'] == "ok") {

                var unreadMsg = data['total_unread_msg']
                updateMsgCounter($('.chat-btn .badge-unread-messages'), unreadMsg)
                $('.chat-btn .chat-icon').removeClass('animated')
                if (Math.floor(unreadMsg) == unreadMsg && $.isNumeric(unreadMsg) && 0 < unreadMsg) {
                    $('.chat-btn .chat-icon').addClass('animated')
                } else {
                    $('.chat-btn .chat-icon').addClass('animated-hover')
                }
                var unread_msg_by_contacts = data['unread_msg_by_contacts']
                if (null != unread_msg_by_contacts && 0 < unread_msg_by_contacts.length) {
                    for (var index in unread_msg_by_contacts) {
                        var unread_info = unread_msg_by_contacts[index]
                        updateMsgCounter($('.contacts .contact-item[data-contactID="' + unread_info.contact_id + '"] .badge-unread-contact-messages'), unread_info.unread_msg)
                    }
                }
            }
        }
    });
}

function updateMsgCounter(element, unreadMsgCount) {
    element.text('')
    element.removeClass('d-none')
    if (Math.floor(unreadMsgCount) == unreadMsgCount && $.isNumeric(unreadMsgCount) && 0 < unreadMsgCount) {
        element.text(unreadMsgCount)
    } else {
        element.addClass('d-none')
    }
}

function loadContactConversation(contactId) {
    if (null != contactId && '' != contactId) {

        markMessagesAsReaded(contactId)
        refreshChatMessages(null, null, contactId, 0)
    }
}

function markMessagesAsReaded(contactId) {
    $.ajax({
        headers: {"X-CSRFToken": getcsrftoken()},
        url: 'ajax/mark_as_read_chat_message/',
        data: {'contact_id': contactId},
        cache: false,
        type: 'POST',
        success: function (data) {

            if (data['status'] == "ok") {
                checkNewChatMessages()
            }
        }
    });
}

function responsePlayerLike(group_artifact_info_id) {
    $.ajax({
        headers: {"X-CSRFToken": getcsrftoken()},
        url: 'ajax/response_player_like/',
        data: {'group_artifact_info_id': group_artifact_info_id},
        cache: false,
        type: 'POST',
        success: function (data) {

            if (data['status'] == "ok") {
                var likeBtn = $('.player-rating-btn[data-gartifact-info-id="group_artifact_info_id"]'.replace('group_artifact_info_id', group_artifact_info_id))
                likeBtn.find('.fa-thumbs-up').toggleClass('far fas')
            }
        }
    });
}

function usersGroupCourseSelected(courseId, year) {
    $.ajax({
        headers: {"X-CSRFToken": getcsrftoken()},
        url: 'ajax/course_selected/',
        data: {'course_id': courseId, 'year': year},
        cache: false,
        type: 'POST',
        success: function (data) {

            if (data['status'] == "ok") {
                $('.users-management-view').html(data['group_table'])
            } else if (data['status'] == "error") {
                add_messages_to_view('error', data['error'])
            }
        }
    });
}

function groupEnabledValueChange(element, group_id) {
    $.ajax({
        headers: {"X-CSRFToken": getcsrftoken()},
        url: 'ajax/group_enable_valuechange/',
        data: {'group_id': group_id},
        cache: false,
        type: 'POST',
        success: function (data) {
            if (data['status'] == "ok") {
                $('.users-management-view').html(data['group_table'])
                add_messages_to_view("success", data['message'])
            } else {
                var msgError = data['error_msg']
                if (msgError) {
                    add_messages_to_view("error", msgError)
                }
            }
        }
    });
}

function usersGroupChanged(group_id, userId, courseId, year, userame) {
    if (0 <= group_id) {
        $.ajax({
            headers: {"X-CSRFToken": getcsrftoken()},
            url: 'ajax/change_usergroup/',
            data: {'group_id': group_id, 'user_id': userId, 'course_id': courseId, 'year': year},
            cache: false,
            type: 'POST',
            success: function (data) {
                if (data['status'] == "ok") {
                    $('.users-management-view').html(data['group_table'])
                    add_messages_to_view("success", data['message'])
                } else {
                    var msgError = data['error_msg']
                    if (msgError) {
                        add_messages_to_view("error", msgError)
                    }
                }
            }
        });
    } else {

        var modal = $('#newGroupModal')
        modal.data('user-id', userId)
        var title = modal.find('.modal-title')
        var msg = title.data('title')
        title.text(msg + userame)
        modal.modal('show')
    }
}

function createNewGroup(groupName, userId, courseId, year) {
    $.ajax({
        headers: {"X-CSRFToken": getcsrftoken()},
        url: 'ajax/create_usergroup/',
        data: {'group_name': groupName, 'user_id': userId, 'course_id': courseId, 'year': year},
        cache: false,
        type: 'POST',
        success: function (data) {
            if (data['status'] == "ok") {
                $('.users-management-view').html(data['group_table'])
                add_messages_to_view("success", data['message'])
            } else {
                var msgError = data['error_msg']
                if (msgError) {
                    add_messages_to_view("error", msgError)
                }
            }
        }
    });

}