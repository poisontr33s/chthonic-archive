#![allow(clippy::needless_pass_by_value)]

use std::alloc::{alloc, dealloc, Layout};
use std::cell::RefCell;

use chthonic_synapse_schema::{
    slot_header_bytes, vertex_stride_bytes, GEO_BG_RGB, GEO_SAFFRON_RGB, PackedSedimentVertex,
    SedimentSlotHeader, SLOT_MAGIC, SLOT_VERSION,
};
use wasm_bindgen::closure::Closure;
use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast;
use web_sys::{HtmlCanvasElement, WebGl2RenderingContext as GL, WebGlBuffer, WebGlProgram, WebGlShader};

thread_local! {
    static LOOM: RefCell<Option<LoomState>> = RefCell::new(None);
}

struct LoomState {
    canvas: HtmlCanvasElement,
    gl: GL,
    program: WebGlProgram,
    vertex_buffer: WebGlBuffer,
    interleaved: Vec<f32>,
    point_count: i32,
    context_lost: bool,
    _lost_listener: Closure<dyn FnMut(web_sys::Event)>,
    _restored_listener: Closure<dyn FnMut(web_sys::Event)>,
}

#[wasm_bindgen]
pub fn init_loom(canvas_id: &str) -> Result<(), JsValue> {
    console_error_panic_hook::set_once();

    let document = web_sys::window()
        .and_then(|win| win.document())
        .ok_or_else(|| JsValue::from_str("window.document unavailable"))?;

    let canvas = document
        .get_element_by_id(canvas_id)
        .ok_or_else(|| JsValue::from_str("canvas element not found"))?
        .dyn_into::<HtmlCanvasElement>()
        .map_err(|_| JsValue::from_str("element is not HtmlCanvasElement"))?;

    let gl = canvas
        .get_context("webgl2")?
        .ok_or_else(|| JsValue::from_str("WebGL2 context unavailable"))?
        .dyn_into::<GL>()
        .map_err(|_| JsValue::from_str("failed to cast WebGL2 context"))?;

    let (program, vertex_buffer) = build_pipeline(&gl)?;

    let lost_listener = Closure::wrap(Box::new(move |event: web_sys::Event| {
        event.prevent_default();
        LOOM.with(|slot| {
            if let Some(state) = slot.borrow_mut().as_mut() {
                state.context_lost = true;
            }
        });
    }) as Box<dyn FnMut(_)>);
    canvas.add_event_listener_with_callback("webglcontextlost", lost_listener.as_ref().unchecked_ref())?;

    let restored_listener = Closure::wrap(Box::new(move |_event: web_sys::Event| {
        LOOM.with(|slot| {
            if let Some(state) = slot.borrow_mut().as_mut() {
                if let Ok((program, vertex_buffer)) = build_pipeline(&state.gl) {
                    state.program = program;
                    state.vertex_buffer = vertex_buffer;
                    state.context_lost = false;
                }
            }
        });
    }) as Box<dyn FnMut(_)>);
    canvas.add_event_listener_with_callback("webglcontextrestored", restored_listener.as_ref().unchecked_ref())?;

    LOOM.with(|slot| {
        *slot.borrow_mut() = Some(LoomState {
            canvas,
            gl,
            program,
            vertex_buffer,
            interleaved: Vec::new(),
            point_count: 0,
            context_lost: false,
            _lost_listener: lost_listener,
            _restored_listener: restored_listener,
        });
    });

    Ok(())
}

#[wasm_bindgen]
pub fn alloc_buffer(len: usize) -> *mut u8 {
    if len == 0 {
        return std::ptr::null_mut();
    }
    let layout = Layout::from_size_align(len, 8).expect("valid layout");
    unsafe { alloc(layout) }
}

#[wasm_bindgen]
pub fn free_buffer(ptr: *mut u8, len: usize) {
    if ptr.is_null() || len == 0 {
        return;
    }
    let layout = Layout::from_size_align(len, 8).expect("valid layout");
    unsafe { dealloc(ptr, layout) };
}

#[wasm_bindgen]
pub fn digest_sediment(ptr: *const u8, len: usize) -> Result<(), JsValue> {
    if ptr.is_null() || len < slot_header_bytes() {
        return Err(JsValue::from_str("invalid sediment buffer"));
    }

    let header = unsafe { &*(ptr as *const SedimentSlotHeader) };
    if header.magic != SLOT_MAGIC || header.version != SLOT_VERSION {
        return Err(JsValue::from_str("invalid sediment frame header"));
    }

    let vertex_count = header.vertex_count as usize;
    let required = slot_header_bytes() + (vertex_count * vertex_stride_bytes());
    if len < required {
        return Err(JsValue::from_str("truncated sediment frame"));
    }

    let vertices_ptr = unsafe { ptr.add(slot_header_bytes()) as *const PackedSedimentVertex };
    let vertices = unsafe { std::slice::from_raw_parts(vertices_ptr, vertex_count) };

    LOOM.with(|slot| {
        let mut binding = slot.borrow_mut();
        let Some(state) = binding.as_mut() else {
            return Err(JsValue::from_str("loom renderer not initialized"));
        };

        if header.chunk_index == 0 || header.total_chunks <= 1 {
            state.interleaved.clear();
        }
        state.interleaved.reserve(state.interleaved.len() + (vertex_count * 7));

        for vertex in vertices {
            // project 3D sediment into NDC-like 2D layout for point rendering.
            let px = (vertex.x * 0.02).clamp(-1.3, 1.3);
            let py = ((vertex.z * 0.02) + (vertex.y * 0.002)).clamp(-1.3, 1.3);
            let size = (vertex.radius * 0.35).clamp(1.0, 18.0);
            let (r, g, b) = if vertex.r <= 0.0 && vertex.g <= 0.0 && vertex.b <= 0.0 {
                (GEO_SAFFRON_RGB[0], GEO_SAFFRON_RGB[1], GEO_SAFFRON_RGB[2])
            } else {
                (
                    vertex.r.clamp(0.0, 1.0),
                    vertex.g.clamp(0.0, 1.0),
                    vertex.b.clamp(0.0, 1.0),
                )
            };

            state.interleaved.extend_from_slice(&[
                px,
                py,
                size,
                r,
                g,
                b,
                vertex.alpha.clamp(0.0, 1.0),
            ]);
        }

        state.point_count = (state.interleaved.len() / 7) as i32;
        Ok(())
    })
}

#[wasm_bindgen]
pub fn render_frame() -> Result<(), JsValue> {
    LOOM.with(|slot| {
        let mut binding = slot.borrow_mut();
        let Some(state) = binding.as_mut() else {
            return Err(JsValue::from_str("loom renderer not initialized"));
        };
        if state.context_lost {
            return Ok(());
        }

        let width = state.canvas.client_width().max(1);
        let height = state.canvas.client_height().max(1);
        state.canvas.set_width(width as u32);
        state.canvas.set_height(height as u32);
        state.gl.viewport(0, 0, width, height);
        state
            .gl
            .clear_color(GEO_BG_RGB[0], GEO_BG_RGB[1], GEO_BG_RGB[2], 1.0);
        state.gl.clear(GL::COLOR_BUFFER_BIT);

        if state.point_count <= 0 {
            return Ok(());
        }

        state.gl.use_program(Some(&state.program));
        state.gl.bind_buffer(GL::ARRAY_BUFFER, Some(&state.vertex_buffer));

        let vertex_data = unsafe { js_sys::Float32Array::view(&state.interleaved) };
        state.gl.buffer_data_with_array_buffer_view(
            GL::ARRAY_BUFFER,
            &vertex_data,
            GL::STREAM_DRAW,
        );

        let stride = 7 * 4;
        state.gl.enable_vertex_attrib_array(0);
        state
            .gl
            .vertex_attrib_pointer_with_i32(0, 2, GL::FLOAT, false, stride, 0);
        state.gl.enable_vertex_attrib_array(1);
        state
            .gl
            .vertex_attrib_pointer_with_i32(1, 1, GL::FLOAT, false, stride, 8);
        state.gl.enable_vertex_attrib_array(2);
        state
            .gl
            .vertex_attrib_pointer_with_i32(2, 4, GL::FLOAT, false, stride, 12);

        state.gl.draw_arrays(GL::POINTS, 0, state.point_count);
        Ok(())
    })
}

fn build_pipeline(gl: &GL) -> Result<(WebGlProgram, WebGlBuffer), JsValue> {
    let vertex_shader = compile_shader(
        gl,
        GL::VERTEX_SHADER,
        r#"#version 300 es
layout(location = 0) in vec2 a_position;
layout(location = 1) in float a_size;
layout(location = 2) in vec4 a_color;
out vec4 v_color;
void main() {
    gl_Position = vec4(a_position, 0.0, 1.0);
    gl_PointSize = a_size;
    v_color = a_color;
}
"#,
    )?;

    let fragment_shader = compile_shader(
        gl,
        GL::FRAGMENT_SHADER,
        r#"#version 300 es
precision mediump float;
in vec4 v_color;
out vec4 out_color;
void main() {
    vec2 p = gl_PointCoord - vec2(0.5);
    float d = dot(p, p);
    if (d > 0.25) {
        discard;
    }
    float glow = smoothstep(0.25, 0.0, d);
    out_color = vec4(v_color.rgb, v_color.a * glow);
}
"#,
    )?;

    let program = link_program(gl, &vertex_shader, &fragment_shader)?;
    let buffer = gl
        .create_buffer()
        .ok_or_else(|| JsValue::from_str("failed to create GL buffer"))?;

    Ok((program, buffer))
}

fn compile_shader(gl: &GL, shader_type: u32, source: &str) -> Result<WebGlShader, JsValue> {
    let shader = gl
        .create_shader(shader_type)
        .ok_or_else(|| JsValue::from_str("unable to create shader"))?;
    gl.shader_source(&shader, source);
    gl.compile_shader(&shader);

    if gl
        .get_shader_parameter(&shader, GL::COMPILE_STATUS)
        .as_bool()
        .unwrap_or(false)
    {
        Ok(shader)
    } else {
        Err(JsValue::from_str(
            &gl.get_shader_info_log(&shader)
                .unwrap_or_else(|| "shader compile failure".to_string()),
        ))
    }
}

fn link_program(gl: &GL, vertex_shader: &WebGlShader, fragment_shader: &WebGlShader) -> Result<WebGlProgram, JsValue> {
    let program = gl
        .create_program()
        .ok_or_else(|| JsValue::from_str("unable to create shader program"))?;

    gl.attach_shader(&program, vertex_shader);
    gl.attach_shader(&program, fragment_shader);
    gl.link_program(&program);

    if gl
        .get_program_parameter(&program, GL::LINK_STATUS)
        .as_bool()
        .unwrap_or(false)
    {
        Ok(program)
    } else {
        Err(JsValue::from_str(
            &gl.get_program_info_log(&program)
                .unwrap_or_else(|| "program link failure".to_string()),
        ))
    }
}
