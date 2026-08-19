import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { GaugeDial } from './GaugeDial';

describe('GaugeDial', () => {
  it('renderiza o valor formatado com a unidade', () => {
    render(
      <GaugeDial value={24.3} min={0} max={40} unit="°C" color="#ff0000" label="temperatura" />
    );
    expect(screen.getByText('24.3 °C')).toBeInTheDocument();
  });

  it('renderiza o label da métrica', () => {
    render(
      <GaugeDial value={24.3} min={0} max={40} unit="°C" color="#ff0000" label="temperatura" />
    );
    expect(screen.getByText('temperatura')).toBeInTheDocument();
  });

  it('anel de progresso tem stroke igual à prop color', () => {
    const { container } = render(
      <GaugeDial value={24.3} min={0} max={40} unit="°C" color="#123456" label="temperatura" />
    );
    // Procuramos o segundo circle, que é o de progresso
    const progressCircle = container.querySelector('.gauge-dial__progress');
    expect(progressCircle).toBeInTheDocument();
    expect(progressCircle).toHaveAttribute('stroke', '#123456');
  });

  it('não deve ultrapassar 100% de preenchimento quando o value é maior que max (clamp)', () => {
    const { container } = render(
      <GaugeDial value={50} min={0} max={40} unit="°C" color="#ff0000" label="temperatura" />
    );
    
    // O tamanho do path (stroke-dasharray) não deve ser maior que o máximo permitido
    // O max arc length (75% da circunferência) é constante
    const SIZE = 120;
    const STROKE = 5;
    const RADIUS = (SIZE - STROKE) / 2;
    const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
    const ARC_LENGTH = CIRCUMFERENCE * 0.75;
    
    const progressCircle = container.querySelector('.gauge-dial__progress');
    expect(progressCircle).toBeInTheDocument();
    
    // Como está clamped para o máximo, o dasharray (que define a proporção preenchida) 
    // deve usar ARC_LENGTH como o valor de preenchimento atual
    const dashArray = progressCircle?.getAttribute('stroke-dasharray');
    const [progressLength] = dashArray ? dashArray.split(' ') : ['0'];
    
    // Permite um pequeno erro de arredondamento nos floats
    expect(parseFloat(progressLength)).toBeCloseTo(ARC_LENGTH, 1);
  });
});
