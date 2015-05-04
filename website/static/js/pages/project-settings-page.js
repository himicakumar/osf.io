'use strict';

var $ = require('jquery');
var bootbox = require('bootbox');
var Raven = require('raven-js');
var ko = require('knockout');

var ProjectSettings = require('js/projectSettings.js');

var $osf = require('js/osfHelpers');
require('css/addonsettings.css');

var ctx = window.contextVars;

// Initialize treebeard grid
var ProjectNotifications = require('js/notificationsTreebeard.js');
var $notificationsMsg = $('#configureNotificationsMessage');
var notificationsURL = ctx.node.urls.api  + 'subscriptions/';
$.ajax({
    url: notificationsURL,
    type: 'GET',
    dataType: 'json'
}).done(function(response) {
    new ProjectNotifications(response);
}).fail(function(xhr, status, error) {
    $notificationsMsg.addClass('text-danger');
    $notificationsMsg.text('Could not retrieve notification settings.');
    Raven.captureMessage('Could not GET notification settings', {
        url: notificationsURL, status: status, error: error
    });
});

// Reusable function to fix affix widths to columns.  
function fixAffixWidth(parent) {
    parent = parent || 'body';
    $(parent + ' .affix').each(function (){
        var el = $(this);
        var colsize = el.parent('div[class^="col-"]').width();
        el.width(colsize);
    });
}

$(document).ready(function() {

    // Apply KO bindings for Node Category Settings   
    var categories = [];
    var keys = Object.keys(window.contextVars.nodeCategories);
    for (var i = 0; i < keys.length; i++) {        
        categories.push({
            label: window.contextVars.nodeCategories[keys[i]],
            value: keys[i]
        });
    }
    var categorySettingsVM = new ProjectSettings.NodeCategorySettings(
        window.contextVars.node.category,
        categories,
        window.contextVars.node.urls.update
    );
    ko.applyBindings(categorySettingsVM, $('#nodeCategorySettings')[0]);

    $(window).resize(function (){ fixAffixWidth(); });
    $('.project-page .panel').on('affixed.bs.affix', function(){ fixAffixWidth(); });

    $('#deleteNode').on('click', function() {
        ProjectSettings.getConfirmationCode(ctx.node.nodeType);
    });

    // TODO: Knockout-ify me
    $('#commentSettings').on('submit', function() {
        var $commentMsg = $('#configureCommentingMessage');

        var $this = $(this);
        var commentLevel = $this.find('input[name="commentLevel"]:checked').val();

        $osf.postJSON(
            ctx.node.urls.api + 'settings/comments/',
            {commentLevel: commentLevel}
        ).done(function() {
            $commentMsg.addClass('text-success');
            $commentMsg.text('Successfully updated settings.');
            window.location.reload();
        }).fail(function() {
            bootbox.alert('Could not set commenting configuration. Please try again.');
        });

        return false;

    });


    // Set up submission for addon selection form
    $('#selectAddonsForm').on('submit', function() {

        var formData = {};
        $('#selectAddonsForm').find('input').each(function(idx, elm) {
            var $elm = $(elm);
            formData[$elm.attr('name')] = $elm.is(':checked');
        });
        var msgElm = $(this).find('.addon-settings-message');
        $.ajax({
            url: ctx.node.urls.api + 'settings/addons/',
            data: JSON.stringify(formData),
            type: 'POST',
            contentType: 'application/json',
            dataType: 'json',
            success: function() {
                msgElm.text('Settings updated').fadeIn();
                window.location.reload();
            }
        });

        return false;

    });

    // Show capabilities modal on selecting an addon; unselect if user
    // rejects terms
    $('.addon-select').on('change', function() {
        var that = this,
            $that = $(that);
        if ($that.is(':checked')) {
            var name = $that.attr('name');
            var capabilities = $('#capabilities-' + name).html();
            if (capabilities) {
                bootbox.confirm(
                    capabilities,
                    function(result) {
                        if (!result) {
                            $(that).attr('checked', false);
                        }
                    }
                );
            }
        }
    });

});
