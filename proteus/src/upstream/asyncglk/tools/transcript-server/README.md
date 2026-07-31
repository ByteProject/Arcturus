Transcript Recording Server
===========================

This is a very simple PHP server for receiving transcripts from GlkOte, which saves them to the file system. It should not be used in production, but might be safe enough for limited private use with beta testers.

You can upload transcript-server.php to a typical cPanel server, or for testing you can run it with PHP's build-in webserver:

```
php -S 127.0.0.1:8001 transcript-server.php
```

Options
-------

If you create a file called `transcript-server-config.json` then you can set these options:

```
{
    "labels": ["STORYFILE", "LABELS"],
    "path": "PATH"
}
```

`labels` is an optional list of storyfile labels. If this option is provided and someone tries to send a transcript for a label that is not in the list, it will be rejected.

`path` is an optional path to where the transcripts will be stored. The default is the current working directory.

The transcript data format
--------------------------

Transcript data is sent as JSON in this format (as a Typescript interface):

```
export interface TranscriptRecordingData {
    /** The transcript record format is always 'simple */
    format: 'simple',
    /** Player input for char and line events */
    input: string,
    /** The label given to this story at the beginning */
    label: string,
    /** Combined output from buffer windows */
    output: string,
    /** Timestamp from when output returned to GlkOte (milliseconds) */
    outtimestamp: number,
    /** Session ID */
    sessionId: string,
    /** Timestamp from when GlkOte event was sent to VM (milliseconds) */
    timestamp: number,
}
```