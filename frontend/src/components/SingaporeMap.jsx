import { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Polygon } from 'react-leaflet';
import L from 'leaflet';
import { scenarioA, scenarioB } from '../data/demoScenarios';
import 'leaflet/dist/leaflet.css';

const scenarioAIcon = L.divIcon({
  className: 'radiating-dot',
  iconSize: [20, 20],
  iconAnchor: [10, 10]
});

const scenarioBIcon = L.divIcon({
  className: 'sequence-dot',
  iconSize: [16, 16],
  iconAnchor: [8, 8]
});

function MapController({ visibleDots, scenario, isViewerOpen }) {
  const map = useMap();
  
  // Track if we just came from a viewer being open to avoid blinking
  const wasViewerOpen = useRef(isViewerOpen);

  useEffect(() => {
    if (isViewerOpen) {
      if (scenario === 'A') {
        map.flyTo([scenarioA.lat, scenarioA.lng], 16, { animate: true, duration: 1.5 });
      } else if (scenario === 'B' && visibleDots > 0) {
        const pt = scenarioB.points[Math.min(visibleDots - 1, scenarioB.points.length - 1)];
        map.flyTo([pt.lat, pt.lng], 16, { animate: true, duration: 1.5 });
      }
    } else if (wasViewerOpen.current && !isViewerOpen) {
      // Zoom out smoothly. Splitting into zoomOut then panTo prevents the extreme lag spike 
      // that flyTo causes when recalculating the massive mask polygon during a curved flight path.
      map.setZoom(12, { animate: true, duration: 1.0 });
      setTimeout(() => {
        if (map) {
          map.panTo([1.3521, 103.8198], { animate: true, duration: 0.5 });
        }
      }, 1000);
    }
    wasViewerOpen.current = isViewerOpen;
  }, [visibleDots, scenario, isViewerOpen, map]);
  return null;
}

const AutoPopupMarker = ({ position, icon, text, onViewClick }) => {
  const markerRef = useRef(null);
  
  useEffect(() => {
    if (markerRef.current) {
      // Small timeout to ensure it renders first
      setTimeout(() => markerRef.current.openPopup(), 100);
    }
  }, []);

  return (
    <Marker position={position} icon={icon} ref={markerRef}>
      <Popup autoClose={false} closeOnClick={false} closeButton={false} autoPan={true}>
        <div style={{ textAlign: 'center', width: '220px', padding: '5px' }}>
          <div style={{ 
            fontWeight: '500', 
            color: '#fff', 
            marginBottom: '15px', 
            fontSize: '15px',
            lineHeight: '1.4',
            letterSpacing: '0.3px'
          }}>
            <span style={{ color: '#ff4d4d', display: 'block', marginBottom: '4px', fontWeight: 'bold', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px' }}>Alert</span>
            {text}
          </div>
          <button 
            style={{ 
              width: '100%', 
              padding: '10px 16px', 
              fontSize: '14px',
              backgroundColor: '#c41e3a',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: '600',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              transition: 'background-color 0.2s'
            }} 
            onMouseOver={(e) => e.target.style.backgroundColor = '#a01830'}
            onMouseOut={(e) => e.target.style.backgroundColor = '#c41e3a'}
            onClick={(e) => {
              e.stopPropagation();
              onViewClick();
            }}
          >
            View Camera
          </button>
        </div>
      </Popup>
    </Marker>
  );
}

const worldBounds = [
  [90, -180],
  [90, 180],
  [-90, 180],
  [-90, -180]
];

export default function SingaporeMap({ scenario, visibleDots, onViewClick, isViewerOpen }) {
  const [sgMask, setSgMask] = useState([]);

  useEffect(() => {
    fetch('/sgp.json')
      .then(res => res.json())
      .then(data => {
        const holes = [];
        const features = data.features || [data];
        features.forEach(feature => {
          if (feature.geometry.type === 'Polygon') {
            holes.push(feature.geometry.coordinates[0].map(c => [c[1], c[0]]));
          } else if (feature.geometry.type === 'MultiPolygon') {
            feature.geometry.coordinates.forEach(poly => {
              holes.push(poly[0].map(c => [c[1], c[0]]));
            });
          }
        });
        setSgMask([worldBounds, ...holes]);
      })
      .catch(err => console.error("Could not load mask", err));
  }, []);

  return (
    <MapContainer 
      center={[1.3521, 103.8198]} 
      zoom={12} 
      style={{ height: '100%', width: '100%', background: '#031525' }}
      zoomControl={false}
      maxBounds={[[1.16, 103.58], [1.48, 104.14]]}
      maxBoundsViscosity={1.0}
      minZoom={11}
    >
      <TileLayer
        attribution='&copy; CARTO'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      
      {sgMask.length > 0 && (
        <Polygon 
          positions={sgMask} 
          pathOptions={{ color: 'transparent', fillColor: '#031525', fillOpacity: 1 }} 
        />
      )}

      <MapController visibleDots={visibleDots} scenario={scenario} isViewerOpen={isViewerOpen} />

      {scenario === 'A' && (
        <AutoPopupMarker 
          position={[scenarioA.lat, scenarioA.lng]} 
          icon={scenarioAIcon}
          text="Suspected drunk driving detected"
          onViewClick={() => onViewClick(`Scenario A - ${scenarioA.roadName}`, 'A')}
        />
      )}

      {scenario === 'B' && visibleDots > 0 && (
        <>
          <AutoPopupMarker 
            position={[scenarioB.points[0].lat, scenarioB.points[0].lng]} 
            icon={scenarioBIcon}
            text="Suspected drunk driving detected"
            onViewClick={() => onViewClick(`Scenario B - ${scenarioB.roadName}`, 'B')}
          />
          {scenarioB.points.slice(1, visibleDots).map((pt, index) => (
            <Marker key={`dot-${index}`} position={[pt.lat, pt.lng]} icon={scenarioBIcon} />
          ))}
        </>
      )}
    </MapContainer>
  );
}