import React from 'react';
import { Link } from 'react-router-dom';

interface Character {
  id: string;
  name: string;
  image: string;
  description: string;
}

const characters: Character[] = [
  {
    id: 'chad',
    name: 'Chad the Alpha',
    image: '/images/characters/chad.jpg',
    description: 'Confident, assertive, and direct. Chad challenges you with bold statements and unwavering confidence.'
  },
  {
    id: 'professor',
    name: 'Professor Hartley',
    image: '/images/characters/professor.jpg',
    description: 'Analytical, thoughtful, and precise. The Professor engages with nuanced arguments and logical reasoning.'
  },
  // Add other characters here
];

const CharacterSelection: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4 text-red-600">Choose Your Opponent</h1>
        <p className="text-xl text-gray-600">
          Select a character and engage in passionate debate...
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {characters.map(character => (
          <Link 
            key={character.id}
            to={`/debate/${character.id}`}
            className="border rounded-lg overflow-hidden shadow-lg transition-transform duration-300 hover:transform hover:scale-105"
          >
            <div className="h-64 overflow-hidden">
              <img
                src={character.image}
                alt={character.name}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="p-6">
              <h2 className="text-xl font-bold mb-2">{character.name}</h2>
              <p className="text-gray-700 mb-4">{character.description}</p>
              <div className="text-blue-600 font-semibold">
                Start Debate →
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default CharacterSelection;
