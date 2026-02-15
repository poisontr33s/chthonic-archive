#![allow(clippy::needless_pass_by_value)]

use serde::Deserialize;
use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast;

#[derive(Debug, Deserialize)]
struct GraphPayload {
    nodes: Vec<GraphNode>,
    edges: Vec<GraphEdge>,
}

#[derive(Debug, Deserialize)]
struct GraphNode {
    id: String,
    entropy: f32,
    degree: f32,
    x: f32,
    y: f32,
}

#[derive(Debug, Deserialize)]
struct GraphEdge {
    source: String,
    target: String,
}

struct RendererState {
    canvas: web_sys::HtmlCanvasElement,
    context_2d: web_sys::CanvasRenderingContext2d,
    webgpu_ready: bool,
}

thread_local! {
    static RENDERER: std::cell::RefCell<Option<RendererState>> = std::cell::RefCell::new(None);
}

#[wasm_bindgen]
pub async fn init_renderer(canvas_id: &str) -> Result<(), JsValue> {
    console_error_panic_hook::set_once();

    let document = web_sys::window()
        .and_then(|win| win.document())
        .ok_or_else(|| JsValue::from_str("window.document unavailable"))?;

    let canvas = document
        .get_element_by_id(canvas_id)
        .ok_or_else(|| JsValue::from_str("canvas element not found"))?
        .dyn_into::<web_sys::HtmlCanvasElement>()
        .map_err(|_| JsValue::from_str("element is not an HtmlCanvasElement"))?;

    let context_2d = canvas
        .get_context("2d")?
        .ok_or_else(|| JsValue::from_str("2d context unavailable"))?
        .dyn_into::<web_sys::CanvasRenderingContext2d>()
        .map_err(|_| JsValue::from_str("failed to cast 2d context"))?;

    #[cfg(feature = "webgpu")]
    let webgpu_ready = probe_webgpu(&canvas).await.is_ok();
    #[cfg(not(feature = "webgpu"))]
    let webgpu_ready = false;

    RENDERER.with(|slot| {
        *slot.borrow_mut() = Some(RendererState {
            canvas,
            context_2d,
            webgpu_ready,
        });
    });

    Ok(())
}

#[wasm_bindgen]
pub fn render_graph(graph_json: &str) -> Result<(), JsValue> {
    let payload = serde_json::from_str::<GraphPayload>(graph_json)
        .map_err(|error| JsValue::from_str(&format!("graph decode failure: {error}")))?;

    RENDERER.with(|slot| {
        let mut borrowed = slot.borrow_mut();
        let state = borrowed
            .as_mut()
            .ok_or_else(|| JsValue::from_str("renderer not initialized"))?;
        draw_graph(state, &payload)?;
        Ok(())
    })
}

fn draw_graph(state: &mut RendererState, payload: &GraphPayload) -> Result<(), JsValue> {
    let width = f64::from(state.canvas.client_width().max(1));
    let height = f64::from(state.canvas.client_height().max(1));
    state.canvas.set_width(width as u32);
    state.canvas.set_height(height as u32);

    state.context_2d.set_fill_style(&JsValue::from_str(if state.webgpu_ready {
        "#130f0c"
    } else {
        "#181311"
    }));
    state.context_2d.fill_rect(0.0, 0.0, width, height);

    let center_x = width / 2.0;
    let center_y = height / 2.0;
    let scale = width.min(height) / 980.0;

    let mut node_index = std::collections::HashMap::new();
    for node in &payload.nodes {
        node_index.insert(node.id.as_str(), node);
    }

    state.context_2d.begin_path();
    state.context_2d.set_stroke_style(&JsValue::from_str("rgba(140,120,92,0.28)"));
    state.context_2d.set_line_width(if state.webgpu_ready { 1.2 } else { 1.0 });
    for edge in &payload.edges {
        let Some(source) = node_index.get(edge.source.as_str()) else {
            continue;
        };
        let Some(target) = node_index.get(edge.target.as_str()) else {
            continue;
        };
        state.context_2d.move_to(
            center_x + (f64::from(source.x) * scale),
            center_y + (f64::from(source.y) * scale),
        );
        state.context_2d.line_to(
            center_x + (f64::from(target.x) * scale),
            center_y + (f64::from(target.y) * scale),
        );
    }
    state.context_2d.stroke();

    for node in &payload.nodes {
        let radius = 2.2 + f64::from(node.degree.min(14.0) * 0.24);
        let (r, g, b) = entropy_rgb(node.entropy);
        state
            .context_2d
            .set_fill_style(&JsValue::from_str(&format!("rgba({r},{g},{b},0.95)")));
        state.context_2d.begin_path();
        state.context_2d.arc(
            center_x + (f64::from(node.x) * scale),
            center_y + (f64::from(node.y) * scale),
            radius,
            0.0,
            std::f64::consts::TAU,
        )?;
        state.context_2d.fill();
    }

    Ok(())
}

fn entropy_rgb(entropy: f32) -> (u8, u8, u8) {
    if entropy >= 0.78 {
        (138, 76, 42)
    } else if entropy >= 0.48 {
        (201, 169, 98)
    } else {
        (124, 174, 103)
    }
}

#[cfg(feature = "webgpu")]
async fn probe_webgpu(canvas: &web_sys::HtmlCanvasElement) -> Result<(), JsValue> {
    let instance = wgpu::Instance::new(&wgpu::InstanceDescriptor {
        backends: wgpu::Backends::BROWSER_WEBGPU,
        ..Default::default()
    });

    let surface = instance
        .create_surface(wgpu::SurfaceTarget::Canvas(canvas.clone()))
        .map_err(|error| JsValue::from_str(&format!("surface creation failed: {error}")))?;

    let adapter = instance
        .request_adapter(&wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::HighPerformance,
            compatible_surface: Some(&surface),
            force_fallback_adapter: false,
        })
        .await
        .map_err(|error| JsValue::from_str(&format!("adapter request failed: {error}")))?;

    let _ = adapter
        .request_device(&wgpu::DeviceDescriptor::default())
        .await
        .map_err(|error| JsValue::from_str(&format!("device request failed: {error}")))?;

    Ok(())
}
