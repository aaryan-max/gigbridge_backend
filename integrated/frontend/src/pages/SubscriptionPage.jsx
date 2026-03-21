import { useState, useEffect } from 'react';
import DashboardHeader from '../components/DashboardHeader';
import DashboardSidebar from '../components/DashboardSidebar';
import { Star, Crown, Check, X } from 'lucide-react';
import './subscription.css';

const SubscriptionPage = () => {
  const [activeSidebar, setActiveSidebar] = useState('subscription');
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);

  const plans = [
    {
      name: 'Basic',
      subtitle: 'Perfect for getting started',
      price: 0,
      priceText: '₹0',
      billingText: 'Free Forever',
      icon: Star,
      isCurrent: true, // Basic is always current plan
      isPopular: false,
      buttonText: 'Current Plan',
      buttonDisabled: true,
      features: [
        '5 Portfolio Projects',
        '10 Job Applies per Month',
        'Standard Search Visibility',
        'Full Messaging Access'
      ]
    },
    {
      name: 'Premium',
      subtitle: 'Best for active artists and freelancers',
      price: 699,
      priceText: '₹699',
      billingText: '/ month',
      icon: Crown,
      isCurrent: false, // Premium is always upgrade option
      isPopular: true,
      buttonText: 'Upgrade Now',
      buttonDisabled: false,
      features: [
        'Unlimited Portfolio',
        'Unlimited Job Applies',
        'Moderate Rank Boost in Search',
        'Premium Profile Badge',
        'Highlight 3 Projects on Profile',
        'Featured Grid Priority Placement',
        'Basic Performance Analytics',
        'Early Job Alerts'
      ]
    }
  ];

  const handleUpgradeClick = (plan) => {
    setSelectedPlan(plan);
    setShowUpgradeModal(true);
  };

  const handleModalClose = () => {
    setShowUpgradeModal(false);
    setSelectedPlan(null);
  };

  const handleProceed = () => {
    // Mock action for now
    console.log('Upgrade to:', selectedPlan?.name);
    handleModalClose();
  };

  return (
    <div className="db-layout">
      <DashboardHeader />
      <div className="db-shell">
        <DashboardSidebar active={activeSidebar} onSelect={setActiveSidebar} />
        <main className="db-main subscription-page">
          {/* Page Header */}
          <div className="subscription-header">
            <h2>Choose Your Plan</h2>
            <p>Select the perfect plan to grow your freelance career and get more opportunities on GigBridge.</p>
          </div>

          {/* Plans Container */}
          <div className="plans-container">
            <div className="plans-grid">
              {plans.map((plan, index) => {
                const Icon = plan.icon;
                return (
                  <div 
                    key={plan.name}
                    className={`plan-card ${plan.isPopular ? 'popular' : ''} ${plan.isCurrent ? 'current' : ''}`}
                  >
                    {/* Popular Badge */}
                    {plan.isPopular && (
                      <div className="popular-badge">
                        Most Popular
                      </div>
                    )}

                    {/* Plan Content */}
                    <div className="plan-content">
                      {/* Icon */}
                      <div className="plan-icon">
                        <Icon className="w-8 h-8" />
                      </div>

                      {/* Plan Title */}
                      <div className="plan-title">
                        <h3>{plan.name}</h3>
                        <p>{plan.subtitle}</p>
                      </div>

                      {/* Price */}
                      <div className="plan-price">
                        <div className="price-amount">
                          <span className="currency">₹</span>
                          <span className="price">{plan.priceText.replace('₹', '')}</span>
                        </div>
                        <div className="billing-text">{plan.billingText}</div>
                      </div>

                      {/* Features */}
                      <div className="plan-features">
                        {plan.features.map((feature, featureIndex) => (
                          <div key={featureIndex} className="feature-item">
                            <Check className="w-4 h-4 text-green-600" />
                            <span>{feature}</span>
                          </div>
                        ))}
                      </div>

                      {/* Button */}
                      <button
                        className={`plan-button ${plan.isCurrent ? 'current' : 'primary'} ${plan.buttonDisabled ? 'disabled' : ''}`}
                        onClick={() => !plan.buttonDisabled && handleUpgradeClick(plan)}
                        disabled={plan.buttonDisabled}
                      >
                        {plan.buttonText}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Upgrade Modal */}
          {showUpgradeModal && (
            <div className="modal-overlay" onClick={handleModalClose}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>Upgrade to Premium</h3>
                  <button className="modal-close" onClick={handleModalClose}>
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <div className="modal-body">
                  <p>This will activate your Premium plan once payment integration is connected.</p>
                  <div className="modal-plan-info">
                    <div className="plan-name">{selectedPlan?.name} Plan</div>
                    <div className="plan-price-modal">{selectedPlan?.priceText} / month</div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button className="btn-secondary" onClick={handleModalClose}>
                    Cancel
                  </button>
                  <button className="btn-primary" onClick={handleProceed}>
                    Proceed
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default SubscriptionPage;
