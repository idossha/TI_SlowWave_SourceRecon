% log_message.m
% Logs messages to both the console and a log file.

function log_message(fid, varargin)
    % log_message - Logs messages to both the console and a log file.
    %
    % Usage:
    %   log_message(fid, 'Message: %s', variable);
    %
    % Inputs:
    %   fid      - File identifier for the log file.
    %   varargin - Format string and variables, similar to fprintf.

    % Create the message string
    msg = sprintf(varargin{:});

    % Write to console
    fprintf('%s\n', msg);

    % Write to log file
    if fid ~= -1
        fprintf(fid, '%s\n', msg);
    end
end
