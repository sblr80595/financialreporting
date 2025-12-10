import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from 'react-query';
import { 
  ChatBubbleLeftRightIcon, 
  PaperAirplaneIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';

const Feedback: React.FC = () => {
  const navigate = useNavigate();
  const [feedback, setFeedback] = useState({
    stage: '',
    area: '',
    comment: ''
  });

  const submitMutation = useMutation(
    (data: any) => apiService.submitFeedback(data),
    {
      onSuccess: () => {
        toast.success('Feedback submitted successfully!');
        setFeedback({ stage: '', area: '', comment: '' });
      },
      onError: (error: any) => {
        toast.error('Failed to submit feedback');
      },
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedback.stage || !feedback.comment) {
      toast.error('Please fill in all required fields');
      return;
    }
    submitMutation.mutate(feedback);
  };

  const stages = [
    'Step 1: Upload Trial Balance',
    'Step 2: Upload Adjustments',
    'Step 3: Apply Adjustments',
    'Step 4: Map Categories',
    'Step 5: Validate 6 Rules',
    'Step 6: Generate Notes',
    'Step 7: Generate P&L',
    // 'Step 8: Generate BS Notes',
    'Step 8: Generate Balance Sheet',
    'Step 9: Generate Cash Flow',
    'General Feedback'
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r rounded-lg shadow-soft" style={{ background: 'linear-gradient(to right, rgb(139, 0, 16), rgb(110, 0, 13))' }}>
        <div className="px-6 py-8">
          <div className="flex items-center">
            <ChatBubbleLeftRightIcon className="h-12 w-12 text-white" />
            <div className="ml-4">
              <h1 className="text-3xl font-bold text-white">
                Feedback & Support
              </h1>
              <p className="mt-2 text-white text-opacity-90">
                Share your observations and feedback
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Feedback Form */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">💬 Submit Feedback</h2>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="stage" className="block text-sm font-medium text-gray-700 mb-2">
              Which stage is this feedback about? *
            </label>
            <select
              id="stage"
              value={feedback.stage}
              onChange={(e) => setFeedback({ ...feedback, stage: e.target.value })}
              className="input-field"
              required
            >
              <option value="">Select a stage...</option>
              {stages.map((stage) => (
                <option key={stage} value={stage}>{stage}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="area" className="block text-sm font-medium text-gray-700 mb-2">
              Area/Component (e.g., GL 34010000, Adjustment #1)
            </label>
            <input
              type="text"
              id="area"
              value={feedback.area}
              onChange={(e) => setFeedback({ ...feedback, area: e.target.value })}
              className="input-field"
              placeholder="Enter specific area or component"
            />
          </div>

          <div>
            <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-2">
              Feedback / Observation *
            </label>
            <textarea
              id="comment"
              value={feedback.comment}
              onChange={(e) => setFeedback({ ...feedback, comment: e.target.value })}
              className="input-field"
              rows={6}
              placeholder="Please provide detailed feedback about your experience..."
              required
            />
          </div>

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="btn-secondary"
            >
              ← Back to Dashboard
            </button>
            
            <button
              type="submit"
              disabled={submitMutation.isLoading}
              className="btn-primary flex items-center space-x-2"
            >
              {submitMutation.isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Submitting...</span>
                </>
              ) : (
                <>
                  <PaperAirplaneIcon className="h-5 w-5" />
                  <span>Submit Feedback</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Feedback Guidelines */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">📝 Feedback Guidelines</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-green-900 mb-2">✅ Good Feedback Includes:</h3>
            <ul className="text-sm text-green-800 space-y-1">
              <li>• Specific issues or observations</li>
              <li>• Steps to reproduce problems</li>
              <li>• Suggestions for improvement</li>
              <li>• Positive feedback on what works well</li>
            </ul>
          </div>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-blue-900 mb-2">💡 Help Us Improve:</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Report any errors or bugs</li>
              <li>• Share workflow suggestions</li>
              <li>• Provide feature requests</li>
              <li>• Rate your overall experience</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Contact Information */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">📞 Additional Support</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <CheckCircleIcon className="h-8 w-8 text-green-600 mx-auto mb-2" />
            <h3 className="text-sm font-medium text-gray-900">Technical Support</h3>
            <p className="text-xs text-gray-500 mt-1">For technical issues and bugs</p>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <CheckCircleIcon className="h-8 w-8 text-blue-600 mx-auto mb-2" />
            <h3 className="text-sm font-medium text-gray-900">Feature Requests</h3>
            <p className="text-xs text-gray-500 mt-1">Suggest new features and improvements</p>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <CheckCircleIcon className="h-8 w-8 text-purple-600 mx-auto mb-2" />
            <h3 className="text-sm font-medium text-gray-900">General Feedback</h3>
            <p className="text-xs text-gray-500 mt-1">Share your overall experience</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Feedback;
