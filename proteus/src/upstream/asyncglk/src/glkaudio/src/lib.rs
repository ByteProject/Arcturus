/*

Glk Audio decoder
=================

Copyright (c) 2024 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

// Heavily based on https://github.com/pdeljanov/Symphonia/blob/master/symphonia/examples/basic-interleaved.rs

use std::io::Cursor;

use symphonia::core::audio::{AudioBufferRef, SampleBuffer};
use symphonia::core::codecs::{Decoder, DecoderOptions};
use symphonia::core::errors::Error;
use symphonia::core::formats::{FormatOptions, FormatReader, SeekMode, SeekTo};
use symphonia::core::io::MediaSourceStream;
use symphonia::core::meta::MetadataOptions;
use symphonia::core::probe::Hint;
use symphonia::core::units::Time;

use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub fn decode(buffer: Box<[u8]>) -> Vec<u8> {
    let src = Cursor::new(buffer);

    // Create the media source stream.
    let mss = MediaSourceStream::new(Box::new(src), Default::default());

    // Use the default options
    let decoder_opts: DecoderOptions = Default::default();
    let format_opts: FormatOptions = Default::default();
    let hint = Hint::new();
    let metadata_opts: MetadataOptions = Default::default();

    // Probe the media source stream for a format.
    let probed = symphonia::default::get_probe().format(&hint, mss, &format_opts, &metadata_opts).unwrap();

    // Get the format reader yielded by the probe operation.
    let mut format = probed.format;

    // Get the default track.
    let track = format.default_track().unwrap();

    // Create a decoder for the track.
    let mut decoder = symphonia::default::get_codecs().make(&track.codec_params, &decoder_opts).unwrap();

    // Store the track identifier, we'll use it to filter packets.
    let track_id = track.id;

    // Get the spec
    let mut spec= None;
    let mut sample_buf = None;
    let _ = decode_one_packet(&mut format, &mut decoder, track_id, |audio_buf: AudioBufferRef| {
        let audio_spec = *audio_buf.spec();
        // Get the capacity of the decoded buffer. Note: This is capacity, not length!
        let duration = audio_buf.capacity() as u64;
        // Create the f32 sample buffer.
        sample_buf = Some(SampleBuffer::<f32>::new(duration, audio_spec));
        spec = Some(audio_spec);
    });
    let spec = spec.unwrap();
    let mut sample_buf = sample_buf.unwrap();

    // Create a WavWriter
    let mut output: Vec<u8> = Vec::new();
    let mut wav_writer = hound::WavWriter::new(Cursor::new(&mut output), hound::WavSpec {
        bits_per_sample: 32,
        channels: spec.channels.count() as u16,
        sample_format: hound::SampleFormat::Float,
        sample_rate: spec.rate,
    }).unwrap();

    // Reset things
    //mss.rewind();
    format.seek(SeekMode::Accurate, SeekTo::Time { time: Time { seconds: 0, frac: 0.0 }, track_id: None }).unwrap();
    decoder.reset();

    loop {
        let finished = decode_one_packet(&mut format, &mut decoder, track_id, |audio_buf| {
            // Copy the decoded audio buffer into the sample buffer in an interleaved format.
            sample_buf.copy_interleaved_ref(audio_buf);

            // The samples may now be access via the `samples()` function.
            for sample in sample_buf.samples() {
                wav_writer.write_sample(*sample).unwrap();
            }
        });
        if finished.unwrap() {
            break
        }
    }

    wav_writer.flush().unwrap();
    drop(wav_writer);

    output
}

fn decode_one_packet<F>(format: &mut Box<dyn FormatReader>, decoder: &mut Box<dyn Decoder>, track_id: u32, func: F) -> symphonia::core::errors::Result<bool>
    where F: FnOnce(AudioBufferRef)
{
    // Get the next packet from the format reader.
    // EOF is unfortunately treated like an error
    // See https://github.com/pdeljanov/Symphonia/issues/134
    let packet = match format.next_packet() {
        Ok(packet) => Ok(Some(packet)),
        Err(Error::IoError(error)) => {
            if error.kind() == std::io::ErrorKind::UnexpectedEof {
                Ok(None)
            }
            else {
                Err(Error::IoError(error))
            }
        },
        Err(error) => Err(error),
    }.unwrap();
    if packet.is_none() {
        return Ok(true);
    }
    let packet = packet.unwrap();

    // If the packet does not belong to the selected track, skip it.
    if packet.track_id() != track_id {
        return Ok(false);
    }

    // Decode the packet into audio samples, ignoring any decode errors.
    match decoder.decode(&packet) {
        Ok(audio_buf) => {
            func(audio_buf);
        }
        Err(Error::DecodeError(_)) => (),
        Err(error) => return Err(error),
    }
    Ok(false)
}