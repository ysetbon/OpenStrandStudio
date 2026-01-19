// Export utilities - Export canvas to various formats
import {CanvasState, Layer, GroupLayer, Strand} from '../types';
import RNFS from 'react-native-fs';
import {bezierPoint} from './bezier';

/**
 * Export canvas as SVG string
 */
export function exportToSVG(
  canvasState: CanvasState,
  width: number,
  height: number,
): string {
  const layers = canvasState.layers;

  // Generate SVG paths
  const svgPaths: string[] = [];

  function processLayer(layer: Layer | GroupLayer, opacity: number = 1) {
    if (!layer.visible) {
      return;
    }

    if ('layers' in layer) {
      // Group layer
      layer.layers.forEach(l => processLayer(l, opacity));
    } else {
      // Regular layer
      const layerOpacity = layer.opacity * opacity;

      layer.strands.forEach(strand => {
        if (!strand.visible) {
          return;
        }

        const pathData = strand.segments
          .map(seg => {
            const {start, control1, control2, end} = seg.bezier;
            return `M ${start.x} ${start.y} C ${control1.x} ${control1.y}, ${control2.x} ${control2.y}, ${end.x} ${end.y}`;
          })
          .join(' ');

        // Add shadow if enabled
        if (strand.style.shadowEnabled) {
          svgPaths.push(
            `<path d="${pathData}" stroke="${strand.style.shadowColor}" stroke-width="${strand.style.width}" stroke-linecap="round" stroke-linejoin="round" fill="none" opacity="${0.5 * layerOpacity}" transform="translate(${strand.style.shadowOffset.x}, ${strand.style.shadowOffset.y})" filter="url(#shadow)" />`,
          );
        }

        // Add main strand
        svgPaths.push(
          `<path d="${pathData}" stroke="${strand.style.color}" stroke-width="${strand.style.width}" stroke-linecap="round" stroke-linejoin="round" fill="none" opacity="${layerOpacity}" />`,
        );
      });
    }
  }

  layers.forEach(layer => processLayer(layer));

  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="shadow">
      <feGaussianBlur stdDeviation="2" />
    </filter>
  </defs>
  ${svgPaths.join('\n  ')}
</svg>`;

  return svg;
}

/**
 * Save SVG to file
 */
export async function saveSVGToFile(
  filename: string,
  svgContent: string,
): Promise<boolean> {
  try {
    const filepath = `${RNFS.DocumentDirectoryPath}/exports/${filename}.svg`;
    const dirPath = `${RNFS.DocumentDirectoryPath}/exports`;

    // Create exports directory if it doesn't exist
    const dirExists = await RNFS.exists(dirPath);
    if (!dirExists) {
      await RNFS.mkdir(dirPath);
    }

    await RNFS.writeFile(filepath, svgContent, 'utf8');
    return true;
  } catch (error) {
    console.error('Failed to save SVG:', error);
    return false;
  }
}

/**
 * Export canvas statistics
 */
export function exportStatistics(canvasState: CanvasState): string {
  let totalStrands = 0;
  let totalLayers = 0;
  let totalGroups = 0;

  function countLayer(layer: Layer | GroupLayer) {
    if ('layers' in layer) {
      totalGroups++;
      layer.layers.forEach(countLayer);
    } else {
      totalLayers++;
      totalStrands += layer.strands.length;
    }
  }

  canvasState.layers.forEach(countLayer);

  const stats = `OpenStrand Studio Project Statistics

Total Layers: ${totalLayers}
Total Groups: ${totalGroups}
Total Strands: ${totalStrands}
Zoom Level: ${canvasState.zoom}
Grid Enabled: ${canvasState.gridEnabled}
Grid Size: ${canvasState.gridSize}

Generated: ${new Date().toISOString()}
`;

  return stats;
}

/**
 * Export as JSON (project format)
 */
export function exportToJSON(canvasState: CanvasState): string {
  return JSON.stringify(canvasState, null, 2);
}

/**
 * Generate shareable link data
 */
export function generateShareData(
  canvasState: CanvasState,
  projectName: string,
): {title: string; message: string; data: string} {
  const stats = exportStatistics(canvasState);
  const json = exportToJSON(canvasState);

  return {
    title: `OpenStrand Studio - ${projectName}`,
    message: `Check out my OpenStrand Studio project: ${projectName}\n\n${stats}`,
    data: json,
  };
}

/**
 * Calculate canvas bounding box
 */
export function getCanvasBoundingBox(canvasState: CanvasState): {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
} {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  function processLayer(layer: Layer | GroupLayer) {
    if (!layer.visible) {
      return;
    }

    if ('layers' in layer) {
      layer.layers.forEach(processLayer);
    } else {
      layer.strands.forEach(strand => {
        if (!strand.visible) {
          return;
        }

        strand.segments.forEach(seg => {
          for (let i = 0; i <= 20; i++) {
            const pt = bezierPoint(seg.bezier, i / 20);
            minX = Math.min(minX, pt.x);
            minY = Math.min(minY, pt.y);
            maxX = Math.max(maxX, pt.x);
            maxY = Math.max(maxY, pt.y);
          }
        });
      });
    }
  }

  canvasState.layers.forEach(processLayer);

  return {minX, minY, maxX, maxY};
}

/**
 * Export canvas with auto-cropping
 */
export function exportToSVGCropped(canvasState: CanvasState): string {
  const bbox = getCanvasBoundingBox(canvasState);
  const padding = 20;

  const width = bbox.maxX - bbox.minX + padding * 2;
  const height = bbox.maxY - bbox.minY + padding * 2;
  const offsetX = -bbox.minX + padding;
  const offsetY = -bbox.minY + padding;

  const layers = canvasState.layers;
  const svgPaths: string[] = [];

  function processLayer(layer: Layer | GroupLayer, opacity: number = 1) {
    if (!layer.visible) {
      return;
    }

    if ('layers' in layer) {
      layer.layers.forEach(l => processLayer(l, opacity));
    } else {
      const layerOpacity = layer.opacity * opacity;

      layer.strands.forEach(strand => {
        if (!strand.visible) {
          return;
        }

        const pathData = strand.segments
          .map(seg => {
            const {start, control1, control2, end} = seg.bezier;
            return `M ${start.x + offsetX} ${start.y + offsetY} C ${control1.x + offsetX} ${control1.y + offsetY}, ${control2.x + offsetX} ${control2.y + offsetY}, ${end.x + offsetX} ${end.y + offsetY}`;
          })
          .join(' ');

        if (strand.style.shadowEnabled) {
          svgPaths.push(
            `<path d="${pathData}" stroke="${strand.style.shadowColor}" stroke-width="${strand.style.width}" stroke-linecap="round" stroke-linejoin="round" fill="none" opacity="${0.5 * layerOpacity}" transform="translate(${strand.style.shadowOffset.x}, ${strand.style.shadowOffset.y})" filter="url(#shadow)" />`,
          );
        }

        svgPaths.push(
          `<path d="${pathData}" stroke="${strand.style.color}" stroke-width="${strand.style.width}" stroke-linecap="round" stroke-linejoin="round" fill="none" opacity="${layerOpacity}" />`,
        );
      });
    }
  }

  layers.forEach(layer => processLayer(layer));

  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="shadow">
      <feGaussianBlur stdDeviation="2" />
    </filter>
  </defs>
  ${svgPaths.join('\n  ')}
</svg>`;

  return svg;
}
