// Bingo Patterns Component

// import React, { useState } from 'react';
import { useNavigate, /*Link*/ } from 'react-router-dom';
import './BingoPatterns.css';

const BingoPatterns = () => {
  const navigate = useNavigate();

  // Pattern definitions with visual representations
  const patterns = [
    {
      id: 'x-pattern',
      name: 'X Pattern',
      description: 'Complete cells in an X pattern (corners and center).',
      points: 35,
      type: 'X',
      cells: [
        [true, false, true],
        [false, true, false],
        [true, false, true]
      ]
    },
    {
      id: 'o-pattern',
      name: 'O Pattern',
      description: 'Complete all cells on the outside edge of the board.',
      points: 35,
      type: 'O',
      cells: [
        [true, true, true],
        [true, false, true],
        [true, true, true]
      ]
    },
    {
      id: 'horizontal',
      name: 'Horizontal Line',
      description: 'Complete any horizontal line of tasks.',
      points: 5,
      type: 'HORIZ',
      cells: [
        [true, true, true],
        [false, false, false],
        [false, false, false]
      ]
    },
    {
      id: 'vertical',
      name: 'Vertical Line',
      description: 'Complete any vertical line of tasks.',
      points: 5,
      type: 'VERT',
      cells: [
        [true, false, false],
        [true, false, false],
        [true, false, false]
      ]
    }
  ];

  return (
    <div className="patterns-container">
      <h1 className="patterns-header">Bingo Patterns</h1>

      <p className="patterns-intro">
        Complete tasks to form letter patterns and earn bonus points! The letter patterns (H, V, X, O) are worth 35 bonus points each, while simple lines (horizontal or vertical) are worth 5 points each.
      </p>

      <div className="patterns-grid">
        {patterns.map((pattern) => (
          <div
            key={pattern.id}
            className="pattern-card"
          >
            <div className="pattern-header">
              <h3 className="pattern-name">{pattern.name}</h3>
              <span className="pattern-points">+{pattern.points} pts</span>
            </div>

            <div className="pattern-visualization">
              {pattern.cells.map((row, rowIndex) => (
                <div key={rowIndex} className="pattern-row">
                  {row.map((cell, cellIndex) => (
                    <div
                      key={cellIndex}
                      className={`pattern-cell ${cell ? 'highlighted' : ''}`}
                    ></div>
                  ))}
                </div>
              ))}
            </div>

              <div className="pattern-details">
                <p>{pattern.description}</p>
                <div className="pattern-badge">
                  {pattern.type === 'X' && '✖️'}
                  {pattern.type === 'O' && '⭕'}
                  {pattern.type === 'HORIZ' && '➖'}
                  {pattern.type === 'VERT' && '⏐'}
                </div>
              </div>
          </div>
        ))}
      </div>

      <div className="patterns-back">
        <button className="back-button" onClick={() => navigate('/bingo')}>
          Back to Bingo Board
        </button>
      </div>
    </div>
  );
};

export default BingoPatterns;